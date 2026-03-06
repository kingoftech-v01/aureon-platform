import React from 'react';
import { RefreshControl } from 'react-native';
import { colors } from '@theme/colors';

interface PullToRefreshProps {
  refreshing: boolean;
  onRefresh: () => void;
}

const PullToRefresh: React.FC<PullToRefreshProps> = ({ refreshing, onRefresh }) => (
  <RefreshControl
    refreshing={refreshing}
    onRefresh={onRefresh}
    tintColor={colors.primary[500]}
    colors={[colors.primary[500]]}
    progressBackgroundColor={colors.background.secondary}
  />
);

export default PullToRefresh;
