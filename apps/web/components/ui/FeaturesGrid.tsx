'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BrainCircuit, 
  Network, 
  Lock, 
  BarChart3, 
  Zap, 
  Sparkles, 
  Globe, 
  MessageSquareQuote, 
  BarChartHorizontal,
  LayoutGrid 
} from 'lucide-react';

type Feature = {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  category: 'ai' | 'security' | 'analytics' | 'workflow';
};

interface FeaturesGridProps {
  title?: string;
  subtitle?: string;
  className?: string;
  animateOnScroll?: boolean;
}

export default function FeaturesGrid({
  title = 'Built with advanced AI technology',
  subtitle = 'Maily combines cutting-edge AI capabilities with industry-leading analytics and security features.',
  className = '',
  animateOnScroll = true,
}: FeaturesGridProps) {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const categories = [
    { id: 'all', label: 'All Features' },
    { id: 'ai', label: 'AI Capabilities', icon: <BrainCircuit className="h-4 w-4" /> },
    { id: 'security', label: 'Security', icon: <Lock className="h-4 w-4" /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'workflow', label: 'Workflow', icon: <LayoutGrid className="h-4 w-4" /> },
  ];

  const features: Feature[] = [
    {
      id: 'cognitive-canvas',
      title: 'Cognitive Canvas',
      description: 'AI-powered design system that adapts layouts and content based on recipient preferences and behavior patterns.',
      icon: <Sparkles className="h-6 w-6" />,
      color: 'bg-blue-500',
      category: 'ai',
    },
    {
      id: 'ai-mesh',
      title: 'AI Mesh Network',
      description: 'Multiple specialized AI agents working in concert to optimize content, timing, and personalization.',
      icon: <Network className="h-6 w-6" />,
      color: 'bg-purple-500',
      category: 'ai',
    },
    {
      id: 'trust-verification',
      title: 'Interactive Trust Verification',
      description: 'Advanced security protocols that analyze content for compliance and verify sender authenticity.',
      icon: <Lock className="h-6 w-6" />,
      color: 'bg-green-500',
      category: 'security',
    },
    {
      id: 'analytics-fusion',
      title: 'Predictive Analytics Fusion',
      description: 'Combines historical data with AI predictions to forecast campaign performance with unprecedented accuracy.',
      icon: <BarChart3 className="h-6 w-6" />,
      color: 'bg-orange-500',
      category: 'analytics',
    },
    {
      id: 'automated-optimization',
      title: 'Continuous Optimization',
      description: 'Real-time adjustments to campaigns based on performance data and recipient engagement patterns.',
      icon: <Zap className="h-6 w-6" />,
      color: 'bg-red-500',
      category: 'workflow',
    },
    {
      id: 'global-reach',
      title: 'Global Localization',
      description: 'Automatic translation and cultural adaptation for international audiences with region-specific optimizations.',
      icon: <Globe className="h-6 w-6" />,
      color: 'bg-teal-500',
      category: 'ai',
    },
    {
      id: 'sentiment-analysis',
      title: 'Sentiment Analysis',
      description: 'Analyze recipient responses and feedback to improve future communications and customer satisfaction.',
      icon: <MessageSquareQuote className="h-6 w-6" />,
      color: 'bg-indigo-500',
      category: 'analytics',
    },
    {
      id: 'engagement-tracking',
      title: 'Advanced Engagement Metrics',
      description: 'Track and analyze recipient interactions beyond opens and clicks, including time spent and content consumption.',
      icon: <BarChartHorizontal className="h-6 w-6" />,
      color: 'bg-amber-500',
      category: 'analytics',
    },
  ];

  const filteredFeatures = activeCategory && activeCategory !== 'all'
    ? features.filter(feature => feature.category === activeCategory)
    : features;

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <section className={`py-20 ${className}`}>
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-12">
          <motion.h2 
            className="text-3xl md:text-4xl font-bold mb-4 gradient-text"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {title}
          </motion.h2>
          <motion.p 
            className="text-lg text-foreground/70 dark:text-foreground-dark/70 max-w-3xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {subtitle}
          </motion.p>
        </div>

        {/* Category filter */}
        <motion.div 
          className="flex flex-wrap justify-center gap-2 mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id === 'all' ? null : category.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 transition-all duration-200 ${
                (category.id === 'all' && !activeCategory) || category.id === activeCategory
                  ? 'bg-primary text-white shadow-lg scale-105'
                  : 'bg-background/50 dark:bg-background-dark/50 hover:bg-background/80 dark:hover:bg-background-dark/80 border border-border/20 dark:border-border-dark/20'
              }`}
            >
              {category.icon && <span>{category.icon}</span>}
              {category.label}
            </button>
          ))}
        </motion.div>

        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          {filteredFeatures.map((feature) => (
            <motion.div
              key={feature.id}
              variants={itemVariants}
              className="group relative overflow-hidden backdrop-blur-sm rounded-xl border border-border/20 dark:border-border-dark/20 hover:border-primary/30 dark:hover:border-primary-dark/30 bg-background/40 dark:bg-background-dark/40 p-6 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1"
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${feature.color} bg-opacity-10 dark:bg-opacity-20 text-white group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-foreground/70 dark:text-foreground-dark/70">{feature.description}</p>
                </div>
              </div>
              
              {/* Category badge */}
              <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full text-xs font-medium bg-background/60 dark:bg-background-dark/60 backdrop-blur-sm border border-border/20 dark:border-border-dark/20">
                {categories.find(c => c.id === feature.category)?.label}
              </div>
              
              {/* Decorative elements */}
              <div className="absolute -bottom-12 -right-12 w-24 h-24 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-xl group-hover:opacity-100 opacity-0 transition-opacity duration-300" />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
} 