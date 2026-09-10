import React from 'react';
import Platform from 'react-native/Libraries/Utilities/Platform';
import StyleSheet from 'react-native/Libraries/StyleSheet/StyleSheet';
import Text from 'react-native/Libraries/Text/Text';
import View from 'react-native/Libraries/Components/View/View';
import type {ViewStyle} from 'react-native/Libraries/StyleSheet/StyleSheetTypes';

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: Platform.OS === 'ios' ? 3 : 2,
    borderRadius: 10,
    backgroundColor: '#d33',
  },
  label: {color: '#fff', fontSize: 11, fontWeight: '600'},
});

export function Badge({count, style}: {count: number; style?: ViewStyle}) {
  return (
    <View style={[styles.badge, style]}>
      <Text style={styles.label}>{count > 99 ? '99+' : count}</Text>
    </View>
  );
}
