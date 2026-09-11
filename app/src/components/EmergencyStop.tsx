import React from 'react';
import { TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';

interface EmergencyStopProps {
  onStop: () => void;
  isLoading?: boolean;
}

export const EmergencyStop: React.FC<EmergencyStopProps> = ({ onStop, isLoading }) => {
  return (
    <TouchableOpacity
      style={styles.button}
      onPress={onStop}
      activeOpacity={0.8}
      disabled={isLoading}
    >
      <View style={styles.square} />
      <Text style={styles.label}>STOP TASK</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.4)',
    paddingVertical: Spacing.xs + 2,
    paddingHorizontal: Spacing.md,
    borderRadius: Spacing.radius.md,
  },
  square: {
    width: 8,
    height: 8,
    backgroundColor: Colors.accent.error,
    borderRadius: 1,
    marginRight: Spacing.xs + 2,
  },
  label: {
    color: Colors.accent.error,
    fontSize: Typography.size.xs,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
});
