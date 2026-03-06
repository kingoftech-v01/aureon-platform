import React from 'react';
import { View, Dimensions, StyleSheet } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { colors } from '@theme/colors';

interface RevenueChartProps {
  data: { labels: string[]; values: number[] };
  height?: number;
}

export function RevenueChart({ data, height = 220 }: RevenueChartProps) {
  const screenWidth = Dimensions.get('window').width - 48;

  return (
    <View style={styles.container}>
      <LineChart
        data={{
          labels: data.labels,
          datasets: [{ data: data.values.length > 0 ? data.values : [0] }],
        }}
        width={screenWidth}
        height={height}
        chartConfig={{
          backgroundColor: 'transparent',
          backgroundGradientFrom: colors.background.primary,
          backgroundGradientTo: colors.background.primary,
          decimalCount: 0,
          color: (opacity = 1) => `rgba(0, 124, 255, ${opacity})`,
          labelColor: () => colors.text.secondary,
          propsForDots: { r: '4', strokeWidth: '2', stroke: colors.primary[500] },
        }}
        bezier
        style={styles.chart}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center' },
  chart: { borderRadius: 16 },
});
