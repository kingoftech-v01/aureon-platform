import React from 'react';
import { View, Dimensions, StyleSheet } from 'react-native';
import { BarChart as RNBarChart } from 'react-native-chart-kit';
import { colors } from '@theme/colors';

interface BarChartProps {
  data: { labels: string[]; values: number[] };
  height?: number;
}

export function BarChart({ data, height = 220 }: BarChartProps) {
  const screenWidth = Dimensions.get('window').width - 48;

  return (
    <View style={styles.container}>
      <RNBarChart
        data={{
          labels: data.labels,
          datasets: [{ data: data.values.length > 0 ? data.values : [0] }],
        }}
        width={screenWidth}
        height={height}
        yAxisLabel="$"
        yAxisSuffix=""
        chartConfig={{
          backgroundColor: 'transparent',
          backgroundGradientFrom: colors.background.primary,
          backgroundGradientTo: colors.background.primary,
          decimalCount: 0,
          color: (opacity = 1) => `rgba(0, 217, 192, ${opacity})`,
          labelColor: () => colors.text.secondary,
          barPercentage: 0.6,
        }}
        style={styles.chart}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center' },
  chart: { borderRadius: 16 },
});
