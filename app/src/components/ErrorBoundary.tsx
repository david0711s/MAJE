import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';

interface Props {
  children: React.ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Fängt Render-Fehler ab und zeigt eine Meldung statt eines weißen Bildschirms.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error('[MAJE] Screen error:', error);
  }

  render() {
    if (this.state.error) {
      return (
        <View style={styles.box}>
          <Text style={styles.title}>Hier ist ein Fehler aufgetreten</Text>
          <Text style={styles.msg}>{this.state.error.message}</Text>
          <TouchableOpacity style={styles.btn} onPress={() => this.setState({ error: null })} activeOpacity={0.8}>
            <Text style={styles.btnText}>Erneut versuchen</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return <>{this.props.children}</>;
  }
}

const styles = StyleSheet.create({
  box: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
    backgroundColor: Colors.bg.base,
  },
  title: {
    color: Colors.text.primary,
    fontSize: Typography.size.md,
    fontWeight: '700',
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  msg: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
    textAlign: 'center',
    marginBottom: Spacing.md,
    lineHeight: 20,
  },
  btn: {
    backgroundColor: Colors.accent.primary,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    borderRadius: Spacing.radius.sm,
  },
  btnText: { color: '#fff', fontWeight: '700', fontSize: Typography.size.sm },
});
