import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { TutorialStep } from './TutorialStep';

interface TutorialStep {
  title: string;
  description: string;
  image?: string;
}

interface TutorialControllerProps {
  onComplete: () => void;
  onSkip: () => void;
  steps: TutorialStep[];
  autoStart?: boolean;
}

export const TutorialController: React.FC<TutorialControllerProps> = ({
  onComplete,
  onSkip,
  steps,
  autoStart = true,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    if (autoStart) {
      const hasSeenTutorial = localStorage.getItem('maily_tutorial_completed');
      if (!hasSeenTutorial) {
        setIsVisible(true);
      }
    }
  }, [autoStart]);

  const handleNext = () => {
    if (currentStep === steps.length - 1) {
      handleComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const handleComplete = () => {
    localStorage.setItem('maily_tutorial_completed', 'true');
    setIsVisible(false);
    onComplete();
  };

  const handleSkip = () => {
    localStorage.setItem('maily_tutorial_completed', 'true');
    setIsVisible(false);
    onSkip();
  };

  if (!isVisible) return null;

  return (
    <TutorialStep
      title={steps[currentStep].title}
      description={steps[currentStep].description}
      image={steps[currentStep].image}
      step={currentStep + 1}
      totalSteps={steps.length}
      onNext={handleNext}
      onPrevious={handlePrevious}
      onSkip={handleSkip}
    />
  );
};

// Default tutorial steps
export const DEFAULT_TUTORIAL_STEPS: TutorialStep[] = [
  {
    title: t('tutorial.welcome.title'),
    description: t('tutorial.welcome.description'),
    image: '/images/tutorial/welcome.png'
  },
  {
    title: t('tutorial.aiFeatures.title'),
    description: t('tutorial.aiFeatures.description'),
    image: '/images/tutorial/ai-features.png'
  },
  {
    title: t('tutorial.emailEditor.title'),
    description: t('tutorial.emailEditor.description'),
    image: '/images/tutorial/email-editor.png'
  },
  {
    title: t('tutorial.analytics.title'),
    description: t('tutorial.analytics.description'),
    image: '/images/tutorial/analytics.png'
  },
  {
    title: t('tutorial.compliance.title'),
    description: t('tutorial.compliance.description'),
    image: '/images/tutorial/compliance.png'
  }
];
