import { motion } from 'framer-motion';
import Image from 'next/image';
import Link from 'next/link';
import { Avatar } from '../components/Avatar';

function BlogPostImage({ title, className = '' }: { title: string; className?: string }) {
  // Generate a consistent background color based on the title
  const backgroundColor = title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360;

  return (
    <div
      className={`relative aspect-[16/9] bg-gradient-to-br ${className}`}
      style={{
        backgroundImage: `linear-gradient(135deg,
          hsl(${backgroundColor}, 70%, 50%),
          hsl(${(backgroundColor + 60) % 360}, 70%, 50%)
        )`,
      }}
    >
      <div className="absolute inset-0 flex items-center justify-center text-4xl font-bold text-white opacity-20">
        Maily
      </div>
    </div>
  );
}

const featuredPost = {
  title: 'The Future of Email Marketing: AI-Driven Personalization',
  excerpt:
    'Discover how artificial intelligence is revolutionizing email marketing and how you can leverage it for better results.',
  author: {
    name: 'Sarah Johnson',
    role: 'CEO & Co-founder',
  },
  date: 'March 1, 2024',
  readTime: '8 min read',
  slug: 'future-of-email-marketing-ai-personalization',
};

const recentPosts = [
  {
    title: '10 Email Marketing Trends to Watch in 2024',
    excerpt:
      'Stay ahead of the curve with these emerging trends that are shaping the future of email marketing.',
    author: {
      name: 'Michael Chen',
    },
    date: 'February 28, 2024',
    readTime: '6 min read',
    slug: 'email-marketing-trends-2024',
    category: 'Trends',
  },
  {
    title: 'How to Create High-Converting Email Campaigns',
    excerpt:
      'Learn the proven strategies and techniques to create email campaigns that drive conversions.',
    author: {
      name: 'Emma Davis',
    },
    date: 'February 25, 2024',
    readTime: '5 min read',
    slug: 'high-converting-email-campaigns',
    category: 'Strategy',
  },
  {
    title: 'The Complete Guide to Email Automation',
    excerpt:
      'Everything you need to know about setting up and optimizing your email automation workflows.',
    author: {
      name: 'James Wilson',
    },
    date: 'February 22, 2024',
    readTime: '10 min read',
    slug: 'complete-guide-email-automation',
    category: 'Guides',
  },
];

const categories = [
  'All',
  'Strategy',
  'Automation',
  'Analytics',
  'Best Practices',
  'Case Studies',
  'Trends',
  'Guides',
];

export default function BlogPage() {
  return (
    <div className="pt-24">
      {/* Hero Section */}
      <section className="from-primary/95 bg-gradient-to-r to-primary py-20 text-white">
        <div className="container mx-auto px-4 text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-6 font-heading text-5xl font-bold"
          >
            Email Marketing Insights
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mx-auto max-w-2xl text-xl text-gray-100"
          >
            Expert tips, guides, and strategies to help you succeed with email marketing.
          </motion.p>
        </div>
      </section>

      {/* Categories */}
      <section className="border-b py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-4">
            {categories.map(category => (
              <button
                key={category}
                className="rounded-full px-4 py-2 text-gray-600 transition hover:bg-gray-50 hover:text-primary"
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Post */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 font-heading text-3xl font-bold">Featured Post</h2>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="grid items-center gap-12 md:grid-cols-2"
          >
            <BlogPostImage title={featuredPost.title} className="overflow-hidden rounded-2xl" />
            <div>
              <Link href={`/blog/${featuredPost.slug}`} className="group block space-y-4">
                <h3 className="font-heading text-3xl font-bold transition group-hover:text-primary">
                  {featuredPost.title}
                </h3>
                <p className="text-lg text-gray-600">{featuredPost.excerpt}</p>
                <div className="flex items-center space-x-4">
                  <Avatar name={featuredPost.author.name} size={48} />
                  <div>
                    <p className="font-medium">{featuredPost.author.name}</p>
                    <p className="text-gray-600">{featuredPost.author.role}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 text-gray-600">
                  <span>{featuredPost.date}</span>
                  <span>•</span>
                  <span>{featuredPost.readTime}</span>
                </div>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Recent Posts */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="mb-12 font-heading text-3xl font-bold">Recent Posts</h2>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {recentPosts.map((post, index) => (
              <motion.article
                key={post.slug}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="overflow-hidden rounded-2xl bg-white shadow-sm transition hover:shadow-md"
              >
                <Link href={`/blog/${post.slug}`} className="group">
                  <BlogPostImage title={post.title} />
                  <div className="p-6">
                    <span className="text-sm font-medium text-primary">{post.category}</span>
                    <h3 className="mb-3 mt-2 font-heading text-xl font-bold transition group-hover:text-primary">
                      {post.title}
                    </h3>
                    <p className="mb-4 text-gray-600">{post.excerpt}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Avatar name={post.author.name} size={32} />
                        <span className="text-sm font-medium">{post.author.name}</span>
                      </div>
                      <div className="text-sm text-gray-600">{post.readTime}</div>
                    </div>
                  </div>
                </Link>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="mb-6 font-heading text-3xl font-bold">Subscribe to Our Newsletter</h2>
          <p className="mx-auto mb-8 max-w-2xl text-xl text-gray-600">
            Get the latest email marketing tips and strategies delivered to your inbox.
          </p>
          <form className="mx-auto max-w-md">
            <div className="flex gap-4">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 rounded-full border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                type="submit"
                className="hover:bg-primary/90 rounded-full bg-primary px-8 py-3 font-medium text-white transition"
              >
                Subscribe
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
