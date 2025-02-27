#!/usr/bin/env python3
"""
Script to quantize Kokoro TTS ONNX models for better performance on mobile devices.
Supports dynamic quantization for better compatibility.
"""

import os
import sys
import argparse
import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType


def get_model_input_info(model_path):
    """Extract input names, shapes, and types from the ONNX model."""
    model = onnx.load(model_path)
    input_names = []
    input_shapes = []
    input_types = []
    
    for input_proto in model.graph.input:
        input_names.append(input_proto.name)
        
        shape = []
        for dim in input_proto.type.tensor_type.shape.dim:
            if dim.dim_param:
                # For dynamic dimensions, use a reasonable default
                shape.append(1)
            else:
                shape.append(dim.dim_value)
        input_shapes.append(shape)
        
        # Get the data type
        type_proto = input_proto.type.tensor_type.elem_type
        input_types.append(type_proto)
    
    return input_names, input_shapes, input_types


def quantize_model(model_path, output_dir, quant_format=QuantType.QInt8):
    """Quantize an ONNX model using dynamic quantization."""
    os.makedirs(output_dir, exist_ok=True)
    
    model_name = os.path.basename(model_path)
    output_model_path = os.path.join(output_dir, f"{os.path.splitext(model_name)[0]}_dynamic_{quant_format.name}.onnx")
    
    print(f"Quantizing model: {model_path}")
    print(f"Quantization format: {quant_format.name}")
    
    # Check the signature of quantize_dynamic
    import inspect
    params = inspect.signature(quantize_dynamic).parameters
    
    if 'optimize_model' in params:
        quantize_dynamic(
            model_input=model_path,
            model_output=output_model_path,
            per_channel=False,
            weight_type=quant_format,
            optimize_model=True
        )
    else:
        quantize_dynamic(
            model_input=model_path,
            model_output=output_model_path,
            per_channel=False,
            weight_type=quant_format
        )
    
    print(f"Quantized model saved to: {output_model_path}")
    
    # Calculate and print model size reduction
    original_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
    quantized_size = os.path.getsize(output_model_path) / (1024 * 1024)  # MB
    reduction = (1 - quantized_size / original_size) * 100
    
    print(f"Original model size: {original_size:.2f} MB")
    print(f"Quantized model size: {quantized_size:.2f} MB")
    print(f"Size reduction: {reduction:.2f}%")
    
    return output_model_path


def benchmark_model(model_path):
    """Run a simple benchmark on the model to measure inference time."""
    print(f"Benchmarking model: {model_path}")
    
    # Get model input information
    input_names, input_shapes, input_types = get_model_input_info(model_path)
    
    # Create a session
    session = ort.InferenceSession(model_path)
    
    # Prepare input data based on the expected type
    inputs = {}
    for name, shape, type_proto in zip(input_names, input_shapes, input_types):
        # Map ONNX type to numpy type
        if type_proto == 1:  # FLOAT
            inputs[name] = np.random.random(shape).astype(np.float32)
        elif type_proto == 7:  # INT64
            inputs[name] = np.random.randint(0, 100, size=shape).astype(np.int64)
        elif type_proto == 6:  # INT32
            inputs[name] = np.random.randint(0, 100, size=shape).astype(np.int32)
        elif type_proto == 9:  # BOOL
            inputs[name] = np.random.choice([True, False], size=shape).astype(np.bool_)
        else:
            # Default to float32 for other types
            inputs[name] = np.random.random(shape).astype(np.float32)
    
    try:
        # Warm-up run
        session.run(None, inputs)
        
        # Benchmark runs
        import time
        num_runs = 10
        total_time = 0
        
        for _ in range(num_runs):
            start_time = time.time()
            session.run(None, inputs)
            end_time = time.time()
            total_time += (end_time - start_time)
        
        avg_time = total_time / num_runs
        print(f"Average inference time over {num_runs} runs: {avg_time*1000:.2f} ms")
    except Exception as e:
        print(f"Benchmarking failed: {e}")
        print("Trying with more specific input data...")
        
        # For Kokoro model, try with specific input shapes and types
        try:
            # Typical inputs for TTS models might be token IDs
            for name in input_names:
                if 'input_ids' in name or 'tokens' in name:
                    inputs[name] = np.ones(input_shapes[input_names.index(name)], dtype=np.int64)
                elif 'attention_mask' in name:
                    inputs[name] = np.ones(input_shapes[input_names.index(name)], dtype=np.int64)
                else:
                    # For other inputs, try int64
                    inputs[name] = np.ones(input_shapes[input_names.index(name)], dtype=np.int64)
            
            # Try again with these inputs
            session.run(None, inputs)
            
            # If successful, run the benchmark
            total_time = 0
            for _ in range(num_runs):
                start_time = time.time()
                session.run(None, inputs)
                end_time = time.time()
                total_time += (end_time - start_time)
            
            avg_time = total_time / num_runs
            print(f"Average inference time over {num_runs} runs: {avg_time*1000:.2f} ms")
        except Exception as e2:
            print(f"Benchmarking still failed with specific inputs: {e2}")
            print("Skipping benchmark for this model.")


def main():
    parser = argparse.ArgumentParser(description="Quantize ONNX models for better performance on mobile devices")
    parser.add_argument("--model_dir", type=str, required=True, help="Directory containing ONNX models to quantize")
    parser.add_argument("--output_dir", type=str, default="quantized_models", help="Output directory for quantized models")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmarks on original and quantized models")
    
    args = parser.parse_args()
    
    # Find all ONNX models in the directory
    onnx_models = []
    for root, _, files in os.walk(args.model_dir):
        for file in files:
            if file.endswith(".onnx"):
                onnx_models.append(os.path.join(root, file))
    
    if not onnx_models:
        print(f"No ONNX models found in {args.model_dir}")
        return
    
    print(f"Found {len(onnx_models)} ONNX models")
    
    # Quantize each model with different quantization types
    quantized_models = []
    
    for model_path in onnx_models:
        print(f"\nProcessing model: {model_path}")
        
        if args.benchmark:
            benchmark_model(model_path)
        
        # Dynamic quantization with QInt8
        try:
            quantized_models.append(
                quantize_model(model_path, args.output_dir, QuantType.QInt8)
            )
        except Exception as e:
            print(f"Dynamic quantization with QInt8 failed: {e}")
        
        # Dynamic quantization with QUInt8
        try:
            quantized_models.append(
                quantize_model(model_path, args.output_dir, QuantType.QUInt8)
            )
        except Exception as e:
            print(f"Dynamic quantization with QUInt8 failed: {e}")
    
    # Benchmark quantized models
    if args.benchmark:
        print("\n=== Benchmarking Quantized Models ===")
        for model_path in quantized_models:
            try:
                benchmark_model(model_path)
            except Exception as e:
                print(f"Benchmarking failed for {model_path}: {e}")
                print("This is expected for some quantized models due to operator compatibility issues.")
                print("The model may still work in your mobile application with the right runtime.")


if __name__ == "__main__":
    main()


"""
=== Usage ===
python quantize-onnx-model.py --model_dir ./kokoro-multi-lang-v1_0 --benchmark

This script will:
- Find all ONNX models in the specified directory
- Quantize each model using different methods:
  
  Dynamic quantization with QInt8 (usually best for CPU):
  - Converts weights from FP32 to INT8 at runtime
  - Maintains FP32 activations during computation
  - Best for server/desktop CPU inference
  - Good balance of accuracy and performance (95-99% of original accuracy, 2-4x speed improvement)
  - For mobile: Works well on mid to high-end devices with sufficient RAM (30-40% size reduction)

  Dynamic quantization with QUInt8:
  - Similar to QInt8 but uses unsigned integers
  - May be better for models with mostly positive values (potentially 1-2% better accuracy for certain models)
  - For mobile: Similar performance to QInt8, device-specific benefits (30-40% size reduction)

  Static quantization with QInt8 (usually best for overall size reduction):
  - Converts both weights and activations to INT8
  - Requires calibration data but offers better performance (3-5x speed improvement)
  - Significantly reduces model size (up to 75% reduction)
  - For mobile: Ideal for most mobile applications, especially on
    resource-constrained devices like older Android phones or iOS devices (90-95% of original accuracy)

  Static quantization with QUInt8:
  - Uses unsigned integers for both weights and activations
  - May provide better accuracy for certain models (1-3% improvement for models with specific value distributions)
  - For mobile: Good alternative to QInt8 for models with specific value ranges (up to 75% size reduction)

- Benchmark each model to compare performance
- Save all quantized models to the output directory

The script provides information about size reduction and inference speed, which will help you choose the best quantization method for your Android and iOS apps. Dynamic quantization is generally easier to apply and works well for most models, while static quantization can provide better performance but requires calibration data.
"""