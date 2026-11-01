import { Pressable, StyleSheet, Text } from 'react-native';
import { GestureDetector, usePanGesture } from 'react-native-gesture-handler';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';

type Props = {
  subject: string;
  preview: string;
  onOpen: () => void;
};

// One row of the inbox list. Users drag it left to reveal the archive action
// underneath; tapping the row opens the message.
export function SwipeRow({ subject, preview, onOpen }: Props) {
  const translateX = useSharedValue(0);

  const pan = usePanGesture({
    activeOffsetX: [-10, 10],
    onUpdate: (e) => {
      translateX.value = Math.min(0, e.translationX);
    },
    onDeactivate: () => {
      translateX.value = withSpring(translateX.value < -120 ? -160 : 0);
    },
  });

  const rowStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View style={[styles.row, rowStyle]}>
        <Pressable onPress={onOpen} style={styles.content}>
          <Text style={styles.subject}>{subject}</Text>
          <Text numberOfLines={1}>{preview}</Text>
        </Pressable>
      </Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  row: { backgroundColor: '#fff' },
  content: { paddingHorizontal: 16, paddingVertical: 12 },
  subject: { fontWeight: '600' },
});
