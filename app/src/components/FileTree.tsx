import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { formatBytes } from '../utils/format';

export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
  modified?: string;
  children?: FileNode[];
}

interface FileTreeProps {
  nodes: FileNode[];
  onSelectFile: (file: FileNode) => void;
  level?: number;
}

export const FileTree: React.FC<FileTreeProps> = ({ nodes, onSelectFile, level = 0 }) => {
  return (
    <View style={styles.container}>
      {nodes.map((node) => (
        <FileTreeNode
          key={node.path}
          node={node}
          onSelectFile={onSelectFile}
          level={level}
        />
      ))}
    </View>
  );
};

interface FileTreeNodeProps {
  node: FileNode;
  onSelectFile: (file: FileNode) => void;
  level: number;
}

const FileTreeNode: React.FC<FileTreeNodeProps> = ({ node, onSelectFile, level }) => {
  const [expanded, setExpanded] = useState(false);

  const getIcon = () => {
    if (node.is_dir) return expanded ? '📂' : '📁';
    const ext = node.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py': return '🐍';
      case 'js':
      case 'ts':
      case 'tsx': return '📜';
      case 'json': return '🧩';
      case 'md': return '📝';
      case 'sh': return '⚙️';
      case 'txt': return '📄';
      default: return '📄';
    }
  };

  const handlePress = () => {
    if (node.is_dir) {
      setExpanded(!expanded);
    } else {
      onSelectFile(node);
    }
  };

  return (
    <View>
      <TouchableOpacity
        style={[styles.row, { paddingLeft: level * 16 + Spacing.sm }]}
        onPress={handlePress}
        activeOpacity={0.7}
      >
        <Text style={styles.icon}>{getIcon()}</Text>
        <Text style={[styles.name, node.is_dir && styles.dirName]} numberOfLines={1}>
          {node.name}
        </Text>
        {!node.is_dir && node.size !== undefined && (
          <Text style={styles.sizeText}>{formatBytes(node.size)}</Text>
        )}
      </TouchableOpacity>

      {node.is_dir && expanded && node.children && (
        <FileTree
          nodes={node.children}
          onSelectFile={onSelectFile}
          level={level + 1}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.xs + 2,
    paddingRight: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
  },
  icon: {
    marginRight: Spacing.xs + 2,
    fontSize: 14,
  },
  name: {
    flex: 1,
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
    fontFamily: Typography.family.mono,
  },
  dirName: {
    color: Colors.text.primary,
    fontWeight: '600',
  },
  sizeText: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    marginLeft: Spacing.sm,
  },
});
