//
//  MockPhoneView.m
//  Heathcote
//
//  Created by Mike Dean on 11/13/15.
//  Copyright © 2015 Fabulae Obscurae. All rights reserved.
//

#import "MockPhoneView.h"

@implementation MockPhoneView

- (id)initWithFrame:(CGRect)frame
{
    CGRect actualFrame = frame;
    
    actualFrame.size.width  += frame.size.width * 0.065;
//    actualFrame.size.height += frame.size.width * 0.45;
    
    // iPhone 4
//    actualFrame.size.height += frame.size.height * 0.15;

    // iPhone 5
    actualFrame.size.height += frame.size.height * 0.25;

    
    self = [super initWithFrame:actualFrame];
    if (self) {
        
        self.backgroundColor = [UIColor whiteColor];
        self.layer.cornerRadius = frame.size.width * 0.124;
        
    }
    return self;
}

@end
