import React from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from 'next-themes';

interface TutorialStepProps {
  title: string;
  description: string;
  image?: string;
  step: number;
  totalSteps: number;
  onNext: () => void;
  onPrevious: () => void;
  onSkip: () => void;
}

export const TutorialStep: React.FC<TutorialStepProps> = ({
  title,
  description,
  image,
  step,
  totalSteps,
  onNext,
  onPrevious,
  onSkip,
}) => {
  const { t } = useTranslation();
  const { theme } = useTheme();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`
          fixed inset-0 z-50 flex items-center justify-center
          bg-black bg-opacity-50 backdrop-blur-sm
        `}
      >
        <div className={`
          relative w-full max-w-2xl p-6 mx-4 rounded-xl shadow-2xl
          ${theme === 'dark' ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'}
        `}>
          {/* Progress bar */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gray-200 rounded-t-xl">
            <div
              className="h-full bg-blue-600 rounded-t-xl transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>

          {/* Step indicator */}
          <div className="flex items-center justify-between mb-4 mt-4">
            <span className="text-sm font-medium text-gray-500">
              {t('tutorial.stepIndicator', { current: step, total: totalSteps })}
            </span>
            <button
              onClick={onSkip}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              {t('tutorial.skip')}
            </button>
          </div>

          {/* Content */}
          <h2 className="text-2xl font-bold mb-4">{title}</h2>
          <p className="text-lg mb-6">{description}</p>

          {/* Tutorial image */}
          {image && (
            <div className="relative w-full h-64 mb-6 rounded-lg overflow-hidden">
              <img
                src={image}
                alt={title}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex justify-between items-center mt-8">
            <button
              onClick={onPrevious}
              disabled={step === 1}
              className={`
                px-4 py-2 rounded-md transition-colors
                ${step === 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'}
              `}
            >
              {t('tutorial.previous')}
            </button>
            <button
              onClick={onNext}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              {step === totalSteps ? t('tutorial.finish') : t('tutorial.next')}
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
