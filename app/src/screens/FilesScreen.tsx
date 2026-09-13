import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Modal,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Share,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { api, getServerUrl, readRemoteFile, uploadFile } from '../api/client';
import { FileTree, FileNode } from '../components/FileTree';
import { formatBytes, formatDateTime } from '../utils/format';

let DocumentPicker: any = null;
try {
  DocumentPicker = require('expo-document-picker');
} catch {
  DocumentPicker = null;
}

export const FilesScreen: React.FC = () => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [loadingContent, setLoadingContent] = useState<boolean>(false);

  const fetchFiles = async () => {
    setIsLoading(true);
    try {
      const data = await api.get('/files/tree');
      setFileTree(Array.isArray(data?.tree) ? data.tree : []);
    } catch (e) {
      console.error('Error fetching file tree:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleSelectFile = async (node: FileNode) => {
    setSelectedFile(node);
    setLoadingContent(true);
    try {
      const res = await readRemoteFile(node.path);
      setFileContent(res.content || '(Leere Datei)');
    } catch (e: any) {
      setFileContent(`Fehler beim Lesen der Datei: ${e?.response?.data?.detail || e?.message || 'Unbekannt'}`);
    } finally {
      setLoadingContent(false);
    }
  };

  const handleUpload = async () => {
    if (!DocumentPicker) {
      Alert.alert('Upload', 'Kein Datei-Picker verfügbar.');
      return;
    }
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: '*/*', copyToCacheDirectory: true, multiple: false });
      if (result?.canceled) return;
      const asset = result?.assets?.[0];
      if (!asset) return;
      await uploadFile({ uri: asset.uri, file: asset.file, name: asset.name || 'upload.bin', mimeType: asset.mimeType }, 'files');
      await fetchFiles();
    } catch (e: any) {
      Alert.alert('Upload fehlgeschlagen', e?.response?.data?.detail || e?.message || 'Fehler');
    }
  };

  const handleShareFile = async () => {
    if (!selectedFile) return;
    try {
      const serverUrl = await getServerUrl();
      const encoded = selectedFile.path.split('/').map(encodeURIComponent).join('/');
      const downloadUrl = `${serverUrl}/files/download/${encoded}`;
      await Share.share({
        message: `MAJE Datei: ${selectedFile.name}\n${downloadUrl}`,
        url: downloadUrl,
      });
    } catch (e) {
      console.error('Error sharing file:', e);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Dateimanager (/maje)</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.uploadButton} onPress={handleUpload}>
            <Text style={styles.uploadText}>⬆ Hochladen</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.refreshButton} onPress={fetchFiles}>
            <Text style={styles.refreshText}>↻</Text>
          </TouchableOpacity>
        </View>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : fileTree.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>Keine Dateien im Verzeichnis /maje vorhanden.</Text>
        </View>
      ) : (
        <ScrollView style={styles.content}>
          <FileTree nodes={fileTree} onSelectFile={handleSelectFile} />
        </ScrollView>
      )}

      {/* File Preview Modal */}
      <Modal visible={!!selectedFile} animationType="slide" transparent={false}>
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <View style={styles.modalHeaderLeft}>
              <Text style={styles.modalFileName} numberOfLines={1}>
                {selectedFile?.name}
              </Text>
              <Text style={styles.modalFileSize}>
                {selectedFile?.size !== undefined ? formatBytes(selectedFile.size) : ''}
              </Text>
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.shareBtn} onPress={handleShareFile}>
                <Text style={styles.shareBtnText}>Teilen</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.closeBtn}
                onPress={() => setSelectedFile(null)}
              >
                <Text style={styles.closeBtnText}>Schließen</Text>
              </TouchableOpacity>
            </View>
          </View>

          {loadingContent ? (
            <View style={styles.center}>
              <ActivityIndicator size="large" color={Colors.accent.primary} />
            </View>
          ) : (
            <ScrollView style={styles.contentViewer} horizontal={false}>
              <Text style={styles.codeViewerText}>{fileContent}</Text>
            </ScrollView>
          )}
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.bg.base,
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
  headerTitle: {
    color: Colors.text.primary,
    fontSize: Typography.size.base,
    fontWeight: '600',
    fontFamily: Typography.family.mono,
  },
  refreshButton: {
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    backgroundColor: Colors.bg.overlay,
    borderRadius: Spacing.radius.sm,
  },
  refreshText: {
    color: Colors.accent.primary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  uploadButton: {
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    backgroundColor: Colors.accent.primaryMuted,
    borderRadius: Spacing.radius.sm,
    borderWidth: 1,
    borderColor: Colors.accent.primary,
  },
  uploadText: {
    color: Colors.accent.primary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: Spacing.sm,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  emptyText: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
    textAlign: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: Colors.bg.base,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.md,
    backgroundColor: Colors.bg.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
  },
  modalHeaderLeft: {
    flex: 1,
    marginRight: Spacing.sm,
  },
  modalFileName: {
    color: Colors.text.primary,
    fontSize: Typography.size.base,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
  modalFileSize: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
  },
  modalActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  shareBtn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    backgroundColor: Colors.bg.overlay,
    borderRadius: Spacing.radius.sm,
  },
  shareBtnText: {
    color: Colors.accent.info,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  closeBtn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    backgroundColor: Colors.bg.overlay,
    borderRadius: Spacing.radius.sm,
  },
  closeBtnText: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  contentViewer: {
    flex: 1,
    padding: Spacing.md,
    backgroundColor: '#0a0a0c',
  },
  codeViewerText: {
    color: Colors.text.primary,
    fontFamily: Typography.family.mono,
    fontSize: Typography.size.xs,
    lineHeight: 18,
  },
});
