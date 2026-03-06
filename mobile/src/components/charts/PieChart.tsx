import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { PieChart as RNPieChart } from 'react-native-chart-kit';
import { colors } from '@theme/colors';

interface PieChartProps {
  data: Array<{ name: string; value: number; color: string }>;
  height?: number;
}

export function PieChart({ data, height = 220 }: PieChartProps) {
  const screenWidth = Dimensions.get('window').width - 48;
  const chartData = data.map((item) => ({
    name: item.name,
    population: item.value,
    color: item.color,
    legendFontColor: colors.text.secondary,
    legendFontSize: 12,
  }));

  return (
    <View style={styles.container}>
      <RNPieChart
        data={chartData}
        width={screenWidth}
        height={height}
        chartConfig={{
          color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
        }}
        accessor="population"
        backgroundColor="transparent"
        paddingLeft="15"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center' },
});
