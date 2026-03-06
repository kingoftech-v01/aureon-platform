module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    'react-native-reanimated/plugin',
    [
      'module-resolver',
      {
        root: ['./src'],
        alias: {
          '@': './src',
          '@components': './src/components',
          '@screens': './src/screens',
          '@services': './src/services',
          '@hooks': './src/hooks',
          '@store': './src/store',
          '@theme': './src/theme',
          '@types': './src/types',
          '@navigation': './src/navigation',
          '@assets': './src/assets',
          '@config': './src/config',
        },
      },
    ],
  ],
};
