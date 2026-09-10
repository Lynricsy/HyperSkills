import React, {useState} from 'react';
import {ScrollView, Text, View, Pressable, Image} from 'react-native';

type FeedRow =
  | {kind: 'post'; id: string; title: string; body: string; avatar: string; createdAt: string}
  | {kind: 'ad'; id: string; sponsor: string; banner: string}
  | {kind: 'divider'; id: string; label: string};

export default function FeedScreen({rows}: {rows: FeedRow[]}) {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <ScrollView style={{flex: 1, backgroundColor: '#fff'}}>
      {rows.map((row, index) => {
        if (row.kind === 'divider') {
          return (
            <View key={index} style={{padding: 8, backgroundColor: '#eee'}}>
              <Text style={{fontSize: 12, color: '#666'}}>{row.label}</Text>
            </View>
          );
        }

        if (row.kind === 'ad') {
          return (
            <View key={index} style={{padding: 12}}>
              <Image source={{uri: row.banner}} style={{width: '100%', height: 180}} />
              <Text>Sponsored by {row.sponsor}</Text>
            </View>
          );
        }

        const formatter = new Intl.DateTimeFormat('en-US', {
          dateStyle: 'medium',
          timeStyle: 'short',
        });

        return (
          <Pressable
            key={index}
            onPress={() => setOpenId(row.id === openId ? null : row.id)}
            style={{padding: 12, flexDirection: 'row', gap: 12}}>
            <Image source={{uri: row.avatar}} style={{width: 48, height: 48, borderRadius: 24}} />
            <View style={{flex: 1}}>
              <Text style={{fontWeight: '600'}}>{row.title}</Text>
              <Text numberOfLines={openId === row.id ? undefined : 2}>{row.body}</Text>
              <Text style={{fontSize: 11, color: '#888'}}>
                {formatter.format(new Date(row.createdAt))}
              </Text>
            </View>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}
