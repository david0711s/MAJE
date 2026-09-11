import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { ChatMode } from '../store/chatStore';

interface ModeSelectorProps {
  currentMode: ChatMode;
  onSelectMode: (mode: ChatMode) => void;
}

export const ModeSelector: React.FC<ModeSelectorProps> = ({ currentMode, onSelectMode }) => {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[styles.segment, currentMode === 'chat' && styles.activeSegment]}
        onPress={() => onSelectMode('chat')}
        activeOpacity={0.8}
      >
        <Text style={[styles.text, currentMode === 'chat' && styles.activeText]}>
          💬 Chat
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.segment, currentMode === 'agent' && styles.activeSegment]}
        onPress={() => onSelectMode('agent')}
        activeOpacity={0.8}
      >
        <Text style={[styles.text, currentMode === 'agent' && styles.activeText]}>
          ⚡ Agent (ReAct)
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: Colors.bg.surface,
    padding: 3,
    borderRadius: Spacing.radius.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
  },
  segment: {
    flex: 1,
    paddingVertical: Spacing.xs + 2,
    alignItems: 'center',
    borderRadius: Spacing.radius.sm,
  },
  activeSegment: {
    backgroundColor: Colors.bg.overlay,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
    borderWidth: 1,
    borderColor: Colors.border.strong,
  },
  text: {
    fontSize: Typography.size.sm,
    fontFamily: Typography.family.sans,
    color: Colors.text.muted,
    fontWeight: '500',
  },
  activeText: {
    color: Colors.text.primary,
    fontWeight: '600',
  },
});
