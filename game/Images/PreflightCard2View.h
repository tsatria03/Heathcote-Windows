//
//  PreflightCard2View.h
//  Heathcote
//
//  Created by Mike Dean on 11/13/15.
//  Copyright © 2015 Fabulae Obscurae. All rights reserved.
//

#import <UIKit/UIKit.h>
#import "PreflightCardView.h"
#import "PauseLabelView.h"

typedef enum {
    
    PreflightCard2StateStart,
    PreflightCard2StateInitialDelay,
    PreflightCard2StateStartLeftSwipe,
    PreflightCard2StateStartFastForward,
    PreflightCard2StateEndFastForward,
    PreflightCard2StateStartRightSwipe,
    PreflightCard2StateStartRewind,
    PreflightCard2StateEndRewind,
    PreflightCard2StateStartDownSwipe,
    PreflightCard2StateStartPause,
    PreflightCard2StateStartUpSwipe,
    PreflightCard2StateEndPause,
    
} PreflightCard2State;

@interface PreflightCard2View : PreflightCardView
{
    PreflightCard2State lastAction;
}

@property PauseLabelView *pauseLabel;

@end
