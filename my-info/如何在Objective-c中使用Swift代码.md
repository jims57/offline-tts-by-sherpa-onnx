Using Swift Code in an Objective-C Project
it's absolutely possible to use Swift code in an Objective-C project. This is called "mixed language development" and Apple has built-in support for it. Here's how to set it up:
1. Add a Swift File to Your Objective-C Project
When you add your first Swift file to an Objective-C project, Xcode will automatically prompt you to create a bridging header. Click "Create Bridging Header" when prompted.
2. Configure the Swift-Objective-C Bridging
Two key files will help with the integration:
a) The Bridging Header (Objective-C → Swift)
This file allows your Swift code to access Objective-C classes. Xcode creates this automatically with a name like [ProjectName]-Bridging-Header.h.

#import "YourObjectiveCClass.h"


b) The Generated Header (Swift → Objective-C)
Xcode automatically generates a header file that exposes your Swift classes to Objective-C. It's named [ProductModuleName]-Swift.h.
3. Import Swift Code in Objective-C
To use your Swift classes in Objective-C files:

#import "YourProjectName-Swift.h"

4. Swift Class Requirements for Objective-C Compatibility
For a Swift class to be usable from Objective-C:

import Foundation

@objc class MySwiftClass: NSObject {
    @objc func myMethod() -> String {
        return "Hello from Swift!"
    }
    
    @objc var myProperty: String = "Swift Property"
}

Key points:
Use the @objc attribute for classes and members you want to expose
Swift classes should inherit from NSObject to be fully usable in Objective-C
Not all Swift features are available in Objective-C (e.g., generics, tuples, enums with associated values)
5. Build Settings
Ensure these build settings are properly configured:
Defines Module = Yes
Product Module Name is set correctly
Objective-C Bridging Header points to your bridging header file
Example Usage
In Objective-C:

#import "YourProject-Swift.h"

@implementation MyObjCClass

- (void)useSwiftClass {
    MySwiftClass *swiftObject = [[MySwiftClass alloc] init];
    NSString *result = [swiftObject myMethod];
    NSLog(@"Result from Swift: %@", result);
    NSLog(@"Swift property: %@", swiftObject.myProperty);
}

@end


This approach allows you to gradually migrate to Swift or use Swift for new features while maintaining your existing Objective-C codebase.