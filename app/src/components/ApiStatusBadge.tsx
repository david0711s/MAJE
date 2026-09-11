import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';

interface ApiStatusBadgeProps {
  provider: string;
  configured: boolean;
}

export const ApiStatusBadge: React.FC<ApiStatusBadgeProps> = ({ provider, configured }) => {
  return (
    <View style={[styles.container, configured ? styles.activeContainer : styles.inactiveContainer]}>
      <View style={[styles.dot, configured ? styles.activeDot : styles.inactiveDot]} />
      <Text style={[styles.text, configured ? styles.activeText : styles.inactiveText]}>
        {provider}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xxs,
    borderRadius: Spacing.radius.full,
    borderWidth: 1,
  },
  activeContainer: {
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
    borderColor: 'rgba(34, 197, 94, 0.3)',
  },
  inactiveContainer: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  activeDot: {
    backgroundColor: Colors.accent.success,
  },
  inactiveDot: {
    backgroundColor: Colors.accent.error,
  },
  text: {
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.sans,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  activeText: {
    color: Colors.accent.success,
  },
  inactiveText: {
    color: Colors.accent.error,
  },
});
