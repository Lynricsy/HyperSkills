import { useState } from 'react'
import { Pressable, StyleSheet, Text } from 'react-native'
import Animated, { Easing, useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated'

// Design-system curve, copied from our web tokens: --ease-out-strong.
const EASE_OUT_STRONG = 'cubic-bezier(0.23, 1, 0.32, 1)'

type Props = {
  title: string
  subtitle: string
  onPress: () => void
}

export function PressableCard({ title, subtitle, onPress }: Props) {
  const [pressed, setPressed] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const badgeOpacity = useSharedValue(0)

  const badgeStyle = useAnimatedStyle(() => ({
    opacity: withTiming(badgeOpacity.value, {
      duration: 180,
      easing: Easing.bezier(0.23, 1, 0.32, 1),
    }),
  }))

  return (
    <Pressable
      onPressIn={() => setPressed(true)}
      onPressOut={() => setPressed(false)}
      onLongPress={() => {
        setExpanded((e) => !e)
        badgeOpacity.value = expanded ? 0 : 1
      }}
      onPress={onPress}
    >
      <Animated.View
        style={[
          styles.card,
          pressed && styles.cardPressed,
          { height: expanded ? 220 : 120 },
          {
            transitionProperty: ['transform', 'height'],
            transitionDuration: 160,
            transitionTimingFunction: EASE_OUT_STRONG,
          },
        ]}
      >
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.subtitle}>{subtitle}</Text>
        <Animated.View style={[styles.badge, badgeStyle]}>
          <Text style={styles.badgeText}>Pinned</Text>
        </Animated.View>
      </Animated.View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    padding: 16,
    backgroundColor: '#fff',
    transform: [{ scale: 1 }],
  },
  cardPressed: { transform: [{ scale: 0.97 }] },
  title: { fontSize: 17, fontWeight: '600' },
  subtitle: { fontSize: 14, color: '#555', marginTop: 4 },
  badge: { position: 'absolute', top: 12, right: 12 },
  badgeText: { fontSize: 12, fontWeight: '600' },
})
