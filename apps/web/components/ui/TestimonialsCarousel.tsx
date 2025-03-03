'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Quote, Star } from 'lucide-react';
import Image from 'next/image';

type Testimonial = {
  id: string;
  content: string;
  author: string;
  role: string;
  company: string;
  companyLogo?: string;
  rating?: number;
  avatar?: string;
};

interface TestimonialsCarouselProps {
  testimonials: Testimonial[];
  title?: string;
  subtitle?: string;
  autoPlay?: boolean;
  interval?: number;
  className?: string;
}

export default function TestimonialsCarousel({
  testimonials,
  title = 'Trusted by marketers worldwide',
  subtitle = 'See what our customers are saying about Maily',
  autoPlay = true,
  interval = 8000,
  className = '',
}: TestimonialsCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(autoPlay);
  const autoPlayTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        handlePrev();
      } else if (e.key === 'ArrowRight') {
        handleNext();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex]);
  
  // Auto-play functionality
  useEffect(() => {
    if (isAutoPlaying) {
      autoPlayTimerRef.current = setInterval(() => {
        setDirection(1);
        setActiveIndex((prevIndex) => (prevIndex + 1) % testimonials.length);
      }, interval);
    }
    
    return () => {
      if (autoPlayTimerRef.current) {
        clearInterval(autoPlayTimerRef.current);
      }
    };
  }, [isAutoPlaying, interval, testimonials.length]);
  
  // Pause auto-play on hover
  const handleMouseEnter = () => {
    if (autoPlay) {
      setIsAutoPlaying(false);
    }
  };
  
  const handleMouseLeave = () => {
    if (autoPlay) {
      setIsAutoPlaying(true);
    }
  };
  
  const handleNext = () => {
    setDirection(1);
    setActiveIndex((prevIndex) => (prevIndex + 1) % testimonials.length);
  };
  
  const handlePrev = () => {
    setDirection(-1);
    setActiveIndex((prevIndex) => (prevIndex - 1 + testimonials.length) % testimonials.length);
  };
  
  const variants = {
    enter: (direction: number) => ({
      x: direction > 0 ? '100%' : '-100%',
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction < 0 ? '100%' : '-100%',
      opacity: 0,
    }),
  };
  
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }).map((_, index) => (
      <Star
        key={index}
        className={`h-4 w-4 ${
          index < rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300 dark:text-gray-600'
        }`}
      />
    ));
  };

  return (
    <section className={`py-24 relative overflow-hidden ${className}`}>
      {/* Background elements */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-radial from-primary/10 to-transparent blur-3xl opacity-60 dark:opacity-40" />
      </div>
      
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center mb-14">
          <motion.h2 
            className="text-3xl md:text-4xl font-bold mb-4 gradient-text"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {title}
          </motion.h2>
          <motion.p 
            className="text-lg text-foreground/70 dark:text-foreground-dark/70 max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {subtitle}
          </motion.p>
        </div>
        
        <div 
          className="relative max-w-4xl mx-auto"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="relative h-[400px] md:h-[350px] overflow-hidden rounded-2xl backdrop-blur-lg">
            <AnimatePresence initial={false} custom={direction} mode="wait">
              <motion.div
                key={activeIndex}
                custom={direction}
                variants={variants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{
                  x: { type: 'spring', stiffness: 300, damping: 30 },
                  opacity: { duration: 0.2 },
                }}
                className="absolute inset-0 flex flex-col items-center justify-center p-6 md:p-12 bg-background/40 dark:bg-background-dark/40 border border-border/20 dark:border-border-dark/20 rounded-2xl shadow-glass"
              >
                <div className="w-full max-w-3xl mx-auto">
                  <div className="mb-6 flex justify-center">
                    <div className="bg-primary/10 dark:bg-primary-dark/20 p-3 rounded-full">
                      <Quote className="h-8 w-8 text-primary dark:text-primary-dark" />
                    </div>
                  </div>
                  
                  <blockquote className="text-center mb-8">
                    <p className="text-xl md:text-2xl font-medium mb-6 leading-relaxed">
                      "{testimonials[activeIndex].content}"
                    </p>
                    
                    {testimonials[activeIndex].rating && (
                      <div className="flex justify-center mb-6">
                        {renderStars(testimonials[activeIndex].rating || 5)}
                      </div>
                    )}
                    
                    <footer className="flex flex-col items-center">
                      {testimonials[activeIndex].avatar && (
                        <div className="mb-3 relative w-14 h-14 overflow-hidden rounded-full border-2 border-primary/20 dark:border-primary-dark/30">
                          <Image
                            src={testimonials[activeIndex].avatar}
                            alt={testimonials[activeIndex].author}
                            fill
                            sizes="56px"
                            className="object-cover"
                            loading="lazy"
                            quality={90}
                          />
                        </div>
                      )}
                      
                      <div className="text-center">
                        <p className="font-semibold text-lg">{testimonials[activeIndex].author}</p>
                        <p className="text-sm text-foreground/60 dark:text-foreground-dark/60">
                          {testimonials[activeIndex].role}, {testimonials[activeIndex].company}
                        </p>
                      </div>
                      
                      {testimonials[activeIndex].companyLogo && (
                        <div className="mt-4 h-8">
                          <Image 
                            src={testimonials[activeIndex].companyLogo} 
                            alt={testimonials[activeIndex].company}
                            width={120}
                            height={32}
                            className="h-full w-auto object-contain"
                            loading="lazy"
                            quality={85}
                          />
                        </div>
                      )}
                    </footer>
                  </blockquote>
                </div>
                
                {/* Progress indicator */}
                <div className="absolute bottom-4 left-0 right-0 flex justify-center space-x-2">
                  {testimonials.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setDirection(index > activeIndex ? 1 : -1);
                        setActiveIndex(index);
                      }}
                      className="p-1 focus:outline-none"
                      aria-label={`Go to testimonial ${index + 1}`}
                    >
                      <div
                        className={`w-12 h-1 rounded-full transition-all duration-300 ${
                          index === activeIndex
                            ? 'bg-primary dark:bg-primary-dark w-12'
                            : 'bg-gray-300 dark:bg-gray-700 w-8'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
          
          {/* Navigation arrows */}
          <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 flex justify-between pointer-events-none">
            <button
              onClick={handlePrev}
              className="transform -translate-x-4 w-12 h-12 rounded-full bg-background/80 dark:bg-background-dark/80 backdrop-blur-md border border-border/20 dark:border-border-dark/20 shadow-lg flex items-center justify-center text-foreground/70 dark:text-foreground-dark/70 hover:text-foreground dark:hover:text-foreground-dark pointer-events-auto transition-all duration-200 hover:scale-110"
              aria-label="Previous testimonial"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={handleNext}
              className="transform translate-x-4 w-12 h-12 rounded-full bg-background/80 dark:bg-background-dark/80 backdrop-blur-md border border-border/20 dark:border-border-dark/20 shadow-lg flex items-center justify-center text-foreground/70 dark:text-foreground-dark/70 hover:text-foreground dark:hover:text-foreground-dark pointer-events-auto transition-all duration-200 hover:scale-110"
              aria-label="Next testimonial"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}