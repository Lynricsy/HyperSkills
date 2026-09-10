// src/native/DeviceInfo.ts
// JS access layer for our in-app native module. The Objective-C side is
// declared with RCT_EXPORT_MODULE(DeviceInfo) and exports:
//
//   RCT_EXPORT_METHOD(getBatteryLevel:(RCTPromiseResolveBlock)resolve
//                              reject:(RCTPromiseRejectBlock)reject)
//   RCT_EXPORT_BLOCKING_SYNCHRONOUS_METHOD(isLowPowerMode)
//   RCT_EXPORT_METHOD(readDeviceReport:(RCTPromiseResolveBlock)resolve
//                               reject:(RCTPromiseRejectBlock)reject)
//
// readDeviceReport walks the filesystem and can take ~400ms.

import {NativeModules} from 'react-native';

const {DeviceInfo} = NativeModules;

export function getBatteryLevel(): Promise<number> {
  return DeviceInfo.getBatteryLevel();
}

export function isLowPowerMode(): boolean {
  return DeviceInfo.isLowPowerMode();
}

export function readDeviceReport(): Promise<string> {
  return DeviceInfo.readDeviceReport();
}

export function describeDevice(): string {
  // Called from a render path in SettingsScreen.
  return isLowPowerMode() ? 'low power' : 'normal';
}
