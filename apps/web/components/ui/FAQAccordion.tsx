'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Search } from 'lucide-react';

type FAQItem = {
  id: string;
  question: string;
  answer: string;
  category?: string;
};

interface FAQAccordionProps {
  faqs: FAQItem[];
  title?: string;
  subtitle?: string;
  allowSearch?: boolean;
  allowFiltering?: boolean;
  categories?: string[];
  className?: string;
}

export default function FAQAccordion({
  faqs,
  title = 'Frequently Asked Questions',
  subtitle = 'Find answers to common questions about Maily',
  allowSearch = true,
  allowFiltering = true,
  categories = ['General', 'Features', 'Pricing', 'Security'],
  className = '',
}: FAQAccordionProps) {
  const [openItems, setOpenItems] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  
  const toggleItem = (id: string) => {
    setOpenItems((prevOpenItems) =>
      prevOpenItems.includes(id)
        ? prevOpenItems.filter((item) => item !== id)
        : [...prevOpenItems, id]
    );
  };
  
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };
  
  const filteredFaqs = faqs.filter((faq) => {
    // Filter by search query
    const matchesSearch = searchQuery
      ? faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    
    // Filter by category
    const matchesCategory = activeCategory
      ? faq.category === activeCategory
      : true;
    
    return matchesSearch && matchesCategory;
  });
  
  return (
    <section className={`py-24 ${className}`}>
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
            className="text-lg text-foreground/70 dark:text-foreground-dark/70 max-w-2xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {subtitle}
          </motion.p>
        </div>
        
        <div className="max-w-3xl mx-auto">
          {/* Search and filter */}
          <div className="mb-8 flex flex-col md:flex-row gap-4">
            {allowSearch && (
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-foreground/40 dark:text-foreground-dark/40" />
                </div>
                <input
                  type="text"
                  placeholder="Search questions..."
                  value={searchQuery}
                  onChange={handleSearch}
                  className="w-full h-12 pl-10 pr-4 rounded-lg bg-background/60 dark:bg-background-dark/60 backdrop-blur-md border border-border/40 dark:border-border-dark/40 focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200"
                />
              </div>
            )}
            
            {allowFiltering && (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setActiveCategory(null)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeCategory === null
                      ? 'bg-primary text-white'
                      : 'bg-background/60 dark:bg-background-dark/60 hover:bg-background dark:hover:bg-background-dark border border-border/40 dark:border-border-dark/40'
                  }`}
                >
                  All
                </button>
                
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => setActiveCategory(category)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      activeCategory === category
                        ? 'bg-primary text-white'
                        : 'bg-background/60 dark:bg-background-dark/60 hover:bg-background dark:hover:bg-background-dark border border-border/40 dark:border-border-dark/40'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* Results count */}
          {(searchQuery || activeCategory) && (
            <div className="mb-6 text-sm text-foreground/60 dark:text-foreground-dark/60">
              Showing {filteredFaqs.length} {filteredFaqs.length === 1 ? 'result' : 'results'}
              {searchQuery && <span> for "{searchQuery}"</span>}
              {activeCategory && <span> in {activeCategory}</span>}
            </div>
          )}
          
          {/* No results */}
          {filteredFaqs.length === 0 && (
            <div className="text-center py-12">
              <p className="text-xl font-medium mb-2">No matching questions found</p>
              <p className="text-foreground/60 dark:text-foreground-dark/60">
                Try adjusting your search or filter to find what you're looking for
              </p>
            </div>
          )}
          
          {/* FAQ items */}
          <div className="space-y-4">
            {filteredFaqs.map((faq) => (
              <motion.div
                key={faq.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="rounded-xl border border-border/20 dark:border-border-dark/20 overflow-hidden bg-background/40 dark:bg-background-dark/40 backdrop-blur-md hover:border-border/40 dark:hover:border-border-dark/40 transition-all duration-200"
              >
                <button
                  onClick={() => toggleItem(faq.id)}
                  className="flex items-center justify-between w-full px-6 py-4 text-left"
                  aria-expanded={openItems.includes(faq.id)}
                >
                  <span className="text-lg font-semibold">{faq.question}</span>
                  <ChevronDown
                    className={`h-5 w-5 text-foreground/60 dark:text-foreground-dark/60 transition-transform duration-300 ${
                      openItems.includes(faq.id) ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                
                <AnimatePresence>
                  {openItems.includes(faq.id) && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-6 pt-2">
                        <div className="h-px w-full bg-border/20 dark:bg-border-dark/20 mb-4" />
                        <div className="prose dark:prose-invert max-w-none">
                          <p className="text-foreground/80 dark:text-foreground-dark/80">
                            {faq.answer}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
} 