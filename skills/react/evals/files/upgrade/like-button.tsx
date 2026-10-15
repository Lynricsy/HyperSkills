'use client'

import { useOptimistic, useState } from 'react'
import { likePin } from './actions'

export function LikeButton({ pinId, initialLikes }: { pinId: string; initialLikes: number }) {
  const [likes, setLikes] = useState(initialLikes)
  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    likes,
    (current: number, delta: number) => current + delta,
  )

  return (
    <button
      type="button"
      onClick={async () => {
        addOptimisticLike(1)
        const saved = await likePin(pinId)
        setLikes(saved.likes)
      }}
    >
      ♥ {optimisticLikes}
    </button>
  )
}
