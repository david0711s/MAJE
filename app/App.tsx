import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Colors } from './src/theme/colors';
import { Typography } from './src/theme/typography';
import { Spacing } from './src/theme/spacing';
import { useInitializeMAJE } from './src/store';

// Screens
import { HomeScreen } from './src/screens/HomeScreen';
import { TaskListScreen } from './src/screens/TaskListScreen';
import { TaskDetailScreen } from './src/screens/TaskDetailScreen';
import { FilesScreen } from './src/screens/FilesScreen';
import { SoulScreen } from './src/screens/SoulScreen';
import { MemoryScreen } from './src/screens/MemoryScreen';
import { MAJEScreen } from './src/screens/MAJEScreen';
import { AutonomyScreen } from './src/screens/AutonomyScreen';
import { CostDashboard } from './src/screens/CostDashboard';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { SetupScreen } from './src/screens/SetupScreen';
import { useSettingsStore } from './src/store/settingsStore';
import { ErrorBoundary } from './src/components/ErrorBoundary';

type TabKey =
  | 'chat'
  | 'tasks'
  | 'files'
  | 'soul'
  | 'maje'
  | 'autonomy'
  | 'costs'
  | 'settings';

interface TabItem {
  key: TabKey;
  label: string;
  icon: string;
}

const TABS: TabItem[] = [
  { key: 'chat', label: 'Chat', icon: '💬' },
  { key: 'tasks', label: 'Tasks', icon: '⚡' },
  { key: 'files', label: 'Dateien', icon: '📁' },
  { key: 'soul', label: 'Soul & Brain', icon: '🧠' },
  { key: 'maje', label: 'Für MAJE', icon: '✨' },
  { key: 'autonomy', label: 'Autonomie', icon: '🤖' },
  { key: 'costs', label: 'Kosten', icon: '📊' },
  { key: 'settings', label: 'Settings', icon: '⚙️' },
];

export default function App() {
  // Initialize WebSocket and Settings
  useInitializeMAJE();

  const initialized = useSettingsStore((s) => s.initialized);
  const isConnected = useSettingsStore((s) => s.isConnected);
  const token = useSettingsStore((s) => s.token);
  const wrongServer = useSettingsStore((s) => s.wrongServer);
  const setupDismissed = useSettingsStore((s) => s.setupDismissed);
  const dismissSetup = useSettingsStore((s) => s.dismissSetup);

  const [activeTab, setActiveTab] = useState<TabKey>('chat');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [soulSubTab, setSoulSubTab] = useState<'soul' | 'memory'>('soul');

  // Einrichtung nur zeigen, wenn noch nichts gespeichert wurde oder die URL
  // offensichtlich kein MAJE-Server ist. Bei kurzzeitig offline laufen die
  // gespeicherten Einstellungen (URL, Token, Keys) normal weiter.
  if (initialized && !setupDismissed && !isConnected && (!token || wrongServer)) {
    return <SetupScreen onDone={dismissSetup} />;
  }

  const handleOpenTaskDetail = (taskId: string) => {
    setSelectedTaskId(taskId);
    setActiveTab('tasks');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <HomeScreen onOpenTaskDetail={handleOpenTaskDetail} />;

      case 'tasks':
        if (selectedTaskId) {
          return (
            <TaskDetailScreen
              taskId={selectedTaskId}
              onBack={() => setSelectedTaskId(null)}
            />
          );
        }
        return <TaskListScreen onSelectTask={(id) => setSelectedTaskId(id)} />;

      case 'files':
        return <FilesScreen />;

      case 'soul':
        return (
          <View style={styles.tabContainer}>
            <View style={styles.subTabHeader}>
              <TouchableOpacity
                style={[styles.subTab, soulSubTab === 'soul' && styles.subTabActive]}
                onPress={() => setSoulSubTab('soul')}
              >
                <Text style={[styles.subTabText, soulSubTab === 'soul' && styles.subTabTextActive]}>
                  Persönlichkeit (Soul)
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.subTab, soulSubTab === 'memory' && styles.subTabActive]}
                onPress={() => setSoulSubTab('memory')}
              >
                <Text style={[styles.subTabText, soulSubTab === 'memory' && styles.subTabTextActive]}>
                  Gedächtnis (Memory)
                </Text>
              </TouchableOpacity>
            </View>
            <View style={styles.flex1}>
              {soulSubTab === 'soul' ? <SoulScreen /> : <MemoryScreen />}
            </View>
          </View>
        );

      case 'maje':
        return <MAJEScreen onNavigateToChat={() => setActiveTab('chat')} />;

      case 'autonomy':
        return <AutonomyScreen />;

      case 'costs':
        return <CostDashboard />;

      case 'settings':
        return <SettingsScreen />;

      default:
        return <HomeScreen onOpenTaskDetail={handleOpenTaskDetail} />;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />

      {/* Screen Content */}
      <View style={styles.content}>
        <ErrorBoundary key={activeTab}>{renderContent()}</ErrorBoundary>
      </View>

      {/* Linear-style Bottom Navigation Bar */}
      <View style={styles.tabBarWrapper}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabBarScroll}
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <TouchableOpacity
                key={tab.key}
                style={[styles.tabButton, isActive && styles.tabButtonActive]}
                onPress={() => {
                  if (activeTab === 'tasks' && tab.key !== 'tasks') {
                    setSelectedTaskId(null);
                  }
                  setActiveTab(tab.key);
                }}
                activeOpacity={0.7}
              >
                <Text style={styles.tabIcon}>{tab.icon}</Text>
                <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                  {tab.label}
                </Text>
                {isActive && <View style={styles.activeIndicator} />}
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.base,
  },
  content: {
    flex: 1,
  },
  flex1: {
    flex: 1,
  },
  tabContainer: {
    flex: 1,
  },
  subTabHeader: {
    flexDirection: 'row',
    backgroundColor: Colors.bg.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
    gap: Spacing.sm,
  },
  subTab: {
    flex: 1,
    paddingVertical: Spacing.xs + 2,
    alignItems: 'center',
    borderRadius: Spacing.radius.sm,
    backgroundColor: Colors.bg.base,
  },
  subTabActive: {
    backgroundColor: Colors.bg.overlay,
    borderWidth: 1,
    borderColor: Colors.border.strong,
  },
  subTabText: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontWeight: '500',
  },
  subTabTextActive: {
    color: Colors.text.primary,
    fontWeight: '600',
  },
  tabBarWrapper: {
    backgroundColor: Colors.bg.surface,
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
    paddingVertical: Spacing.xs,
  },
  tabBarScroll: {
    paddingHorizontal: Spacing.sm,
    gap: Spacing.xs,
    alignItems: 'center',
  },
  tabButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: Spacing.radius.md,
    minWidth: 64,
    position: 'relative',
  },
  tabButtonActive: {
    backgroundColor: Colors.bg.overlay,
  },
  tabIcon: {
    fontSize: 16,
    marginBottom: 2,
  },
  tabLabel: {
    color: Colors.text.muted,
    fontSize: 11,
    fontFamily: Typography.family.sans,
    fontWeight: '500',
  },
  tabLabelActive: {
    color: Colors.text.primary,
    fontWeight: '600',
  },
  activeIndicator: {
    position: 'absolute',
    bottom: -Spacing.xs + 2,
    width: 16,
    height: 2,
    backgroundColor: Colors.accent.primary,
    borderRadius: 1,
  },
});
