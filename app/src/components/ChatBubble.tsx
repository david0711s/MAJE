import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { ChatMessage } from '../store/chatStore';
import { ReasoningLog } from './ReasoningLog';
import { formatDateTime, formatEUR } from '../utils/format';

interface ChatBubbleProps {
  message: ChatMessage;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
      {!isUser && (
        <View style={styles.assistantHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>M</Text>
          </View>
          <Text style={styles.assistantName}>MAJE</Text>
          {message.mode === 'agent' && (
            <View style={styles.agentTag}>
              <Text style={styles.agentTagText}>AGENT</Text>
            </View>
          )}
          {message.model_used && (
            <Text style={styles.modelTag}>{message.model_used}</Text>
          )}
          {message.cost_eur !== undefined && message.cost_eur > 0 && (
            <Text style={styles.costTag}>{formatEUR(message.cost_eur)}</Text>
          )}
        </View>
      )}

      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.messageText, isUser ? styles.userText : styles.assistantText]}>
          {message.content}
        </Text>

        {/* Render reasoning steps if available */}
        {message.reasoningSteps && message.reasoningSteps.length > 0 && (
          <ReasoningLog steps={message.reasoningSteps} />
        )}
      </View>

      <Text style={[styles.timestamp, isUser && styles.userTimestamp]}>
        {formatDateTime(message.timestamp)}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: Spacing.xs + 2,
    paddingHorizontal: Spacing.md,
    maxWidth: '100%',
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  assistantHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
    gap: 6,
  },
  avatar: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: Colors.accent.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '700',
  },
  assistantName: {
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  agentTag: {
    backgroundColor: Colors.accent.primaryMuted,
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 3,
  },
  agentTagText: {
    color: Colors.accent.primary,
    fontSize: 9,
    fontWeight: '700',
  },
  modelTag: {
    color: Colors.text.muted,
    fontSize: 10,
    fontFamily: Typography.family.mono,
  },
  costTag: {
    color: Colors.accent.warning,
    fontSize: 10,
    fontFamily: Typography.family.mono,
  },
  bubble: {
    padding: Spacing.sm + 2,
    borderRadius: Spacing.radius.lg,
    maxWidth: '88%',
  },
  userBubble: {
    backgroundColor: Colors.accent.primary,
    borderBottomRightRadius: 2,
  },
  assistantBubble: {
    backgroundColor: Colors.bg.surface,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    borderBottomLeftRadius: 2,
    width: '100%',
  },
  messageText: {
    fontSize: Typography.size.base,
    fontFamily: Typography.family.sans,
    lineHeight: 22,
  },
  userText: {
    color: '#ffffff',
  },
  assistantText: {
    color: Colors.text.primary,
  },
  timestamp: {
    fontSize: Typography.size.xs - 2,
    color: Colors.text.muted,
    marginTop: 3,
  },
  userTimestamp: {
    textAlign: 'right',
  },
});
