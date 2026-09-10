import React from 'react';
import { Image, Pressable, Text, View } from 'react-native';
import { FlashList } from '@shopify/flash-list';

type Product = { id: string; name: string; price: number; thumb: string };

export function ProductList({
  products,
  onOpen,
}: {
  products: Product[];
  onOpen: (id: string) => void;
}) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => (
        <Pressable
          style={{ flexDirection: 'row', padding: 12 }}
          onPress={() => onOpen(item.id)}
        >
          <Image source={{ uri: item.thumb }} style={{ width: 64, height: 64 }} />
          <View style={{ marginLeft: 12 }}>
            <Text numberOfLines={2}>{item.name}</Text>
            <Text>{new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(item.price)}</Text>
          </View>
        </Pressable>
      )}
    />
  );
}
