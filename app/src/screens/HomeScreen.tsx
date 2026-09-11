import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { useChatStore } from '../store/chatStore';
import { useSettingsStore } from '../store/settingsStore';
import { ChatBubble } from '../components/ChatBubble';
import { ModeSelector } from '../components/ModeSelector';
import { EmergencyStop } from '../components/EmergencyStop';

interface HomeScreenProps {
  onOpenTaskDetail?: (taskId: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onOpenTaskDetail }) => {
  const [inputText, setInputText] = useState('');
  const flatListRef = useRef<FlatList>(null);

  const {
    messages,
    mode,
    setMode,
    sendMessage,
    isLoading,
    activeTaskId,
    stopActiveTask,
    error,
  } = useChatStore();

  const isConnected = useSettingsStore((s) => s.isConnected);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;
    const text = inputText;
    setInputText('');
    await sendMessage(text);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        {/* Top App Bar */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={[styles.statusDot, isConnected ? styles.dotGreen : styles.dotRed]} />
            <Text style={styles.headerTitle}>MAJE</Text>
            <Text style={styles.serverStatus}>
              {isConnected ? 'ONLINE' : 'OFFLINE'}
            </Text>
          </View>

          {activeTaskId && (
            <View style={styles.headerRight}>
              <EmergencyStop onStop={stopActiveTask} />
            </View>
          )}
        </View>

        {/* Mode Selector Segmented Control */}
        <View style={styles.selectorWrapper}>
          <ModeSelector currentMode={mode} onSelectMode={setMode} />
        </View>

        {/* Active Task Banner if running */}
        {activeTaskId && (
          <TouchableOpacity
            style={styles.taskBanner}
            onPress={() => onOpenTaskDetail?.(activeTaskId)}
            activeOpacity={0.8}
          >
            <View style={styles.taskBannerContent}>
              <View style={styles.pulsingDot} />
              <Text style={styles.taskBannerText} numberOfLines={1}>
                Aktiver Task läuft... (Antippen für Details)
              </Text>
            </View>
            <Text style={styles.taskBannerChevron}>›</Text>
          </TouchableOpacity>
        )}

        {/* Chat Messages */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <ChatBubble message={item} />}
          contentContainerStyle={styles.listContent}
          keyboardShouldPersistTaps="handled"
        />

        {/* Error notification */}
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={
              mode === 'chat'
                ? 'Schreibe MAJE eine Nachricht...'
                : 'Gib MAJE eine komplexe Agent-Aufgabe...'
            }
            placeholderTextColor={Colors.text.muted}
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={2000}
            editable={!isLoading || mode === 'chat'}
          />

          <TouchableOpacity
            style={[
              styles.sendButton,
              (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
            ]}
            onPress={handleSend}
            disabled={!inputText.trim() || isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <Text style={styles.sendIcon}>↑</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.bg.base,
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
    backgroundColor: Colors.bg.surface,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs + 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  dotGreen: {
    backgroundColor: Colors.accent.success,
  },
  dotRed: {
    backgroundColor: Colors.accent.error,
  },
  headerTitle: {
    fontSize: Typography.size.md,
    fontWeight: '700',
    color: Colors.text.primary,
    fontFamily: Typography.family.sans,
    letterSpacing: 0.5,
  },
  serverStatus: {
    fontSize: Typography.size.xs - 2,
    color: Colors.text.muted,
    fontFamily: Typography.family.mono,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  selectorWrapper: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
  },
  taskBanner: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    borderColor: 'rgba(99, 102, 241, 0.3)',
    borderWidth: 1,
    marginHorizontal: Spacing.md,
    marginVertical: Spacing.xs,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs + 2,
    borderRadius: Spacing.radius.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  taskBannerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  pulsingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.accent.primary,
    marginRight: Spacing.xs + 2,
  },
  taskBannerText: {
    color: Colors.accent.primary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
    flex: 1,
  },
  taskBannerChevron: {
    color: Colors.accent.primary,
    fontSize: Typography.size.base,
    marginLeft: Spacing.xs,
  },
  listContent: {
    paddingVertical: Spacing.sm,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
    borderWidth: 1,
    marginHorizontal: Spacing.md,
    marginBottom: Spacing.xs,
    padding: Spacing.sm,
    borderRadius: Spacing.radius.sm,
  },
  errorText: {
    color: Colors.accent.error,
    fontSize: Typography.size.xs,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.bg.surface,
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
    gap: Spacing.sm,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.bg.base,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    borderRadius: Spacing.radius.lg,
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.sm,
    paddingBottom: Spacing.sm,
    color: Colors.text.primary,
    fontSize: Typography.size.base,
    maxHeight: 120,
    minHeight: 44,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.accent.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.bg.overlay,
  },
  sendIcon: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700',
  },
});
