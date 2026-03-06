/**
 * ContractDetailScreen - Contract detail with milestones
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { RouteProp } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useQuery } from '@tanstack/react-query';
import { GlassCard, GlassHeader } from '@components/glass';
import { Badge, CurrencyText, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { contractService } from '@services/contractService';

const ContractDetailScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
  const { contractId } = route.params;
  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', contractId],
    queryFn: () => contractService.getContract(contractId),
  });

  if (isLoading || !contract) return <LoadingSpinner />;

  const completedMilestones = contract.milestones?.filter(m => m.is_completed).length || 0;
  const totalMilestones = contract.milestones?.length || 0;
  const progress = totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0;

  return (
    <View style={styles.container}>
      <GlassHeader title={contract.contract_number} onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Badge label={contract.status} variant={contract.status === 'active' ? 'success' : 'info'} size="md" />
            <Text style={styles.title}>{contract.title}</Text>
            <CurrencyText amount={contract.total_value} currency={contract.currency} size="xl" />

            {/* Progress */}
            <View style={styles.progressSection}>
              <View style={styles.progressHeader}>
                <Text style={styles.progressLabel}>Progress</Text>
                <Text style={styles.progressValue}>{Math.round(progress)}%</Text>
              </View>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${progress}%` }]} />
              </View>
              <Text style={styles.milestoneCount}>{completedMilestones}/{totalMilestones} milestones</Text>
            </View>
          </View>
        </GlassCard>

        {/* Milestones */}
        {contract.milestones && contract.milestones.length > 0 && (
          <GlassCard preset="cardSolid" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.sectionTitle}>Milestones</Text>
              {contract.milestones.map((milestone, index) => (
                <View key={milestone.id} style={styles.milestone}>
                  <View style={[styles.milestoneIcon, milestone.is_completed && styles.milestoneCompleted]}>
                    <Icon name={milestone.is_completed ? 'checkmark' : 'ellipse-outline'} size={16}
                      color={milestone.is_completed ? colors.white : colors.text.muted} />
                  </View>
                  <View style={styles.milestoneInfo}>
                    <Text style={[styles.milestoneTitle, milestone.is_completed && styles.completedText]}>
                      {milestone.title}
                    </Text>
                    {milestone.due_date && (
                      <Text style={styles.milestoneDate}>Due: {new Date(milestone.due_date).toLocaleDateString()}</Text>
                    )}
                  </View>
                  <CurrencyText amount={milestone.amount} size="sm" />
                </View>
              ))}
            </View>
          </GlassCard>
        )}

        {contract.description && (
          <GlassCard preset="cardSolid" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.sectionTitle}>Description</Text>
              <Text style={styles.description}>{contract.description}</Text>
            </View>
          </GlassCard>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  scrollContent: { padding: 20, paddingBottom: 100 },
  card: { marginBottom: 16 },
  cardContent: { padding: 20 },
  title: { fontFamily: fontFamily.bold, fontSize: fontSize['2xl'], color: colors.text.primary, marginVertical: 8 },
  sectionTitle: { fontFamily: fontFamily.semiBold, fontSize: fontSize.xl, color: colors.text.primary, marginBottom: 16 },
  progressSection: { marginTop: 16 },
  progressHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  progressLabel: { fontFamily: fontFamily.medium, fontSize: fontSize.sm, color: colors.text.secondary },
  progressValue: { fontFamily: fontFamily.semiBold, fontSize: fontSize.sm, color: colors.primary[500] },
  progressBar: { height: 8, borderRadius: 4, backgroundColor: colors.figma.lighterElements },
  progressFill: { height: 8, borderRadius: 4, backgroundColor: colors.primary[500] },
  milestoneCount: { fontFamily: fontFamily.regular, fontSize: fontSize.sm, color: colors.text.muted, marginTop: 4 },
  milestone: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.figma.lighterElements + '40' },
  milestoneIcon: { width: 28, height: 28, borderRadius: 14, backgroundColor: colors.figma.lighterElements, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  milestoneCompleted: { backgroundColor: colors.success },
  milestoneInfo: { flex: 1 },
  milestoneTitle: { fontFamily: fontFamily.medium, fontSize: fontSize.md, color: colors.text.primary },
  completedText: { textDecorationLine: 'line-through', color: colors.text.muted },
  milestoneDate: { fontFamily: fontFamily.regular, fontSize: fontSize.sm, color: colors.text.secondary, marginTop: 2 },
  description: { fontFamily: fontFamily.regular, fontSize: fontSize.md, color: colors.text.primary, lineHeight: 22 },
});

export default ContractDetailScreen;
