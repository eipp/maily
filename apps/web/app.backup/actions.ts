'use server';

import { revalidatePath } from 'next/cache';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { z } from 'zod';

/**
 * Form schema for email subscription
 */
const SubscribeSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  marketingConsent: z.boolean().default(false),
});

type SubscribeFormData = z.infer<typeof SubscribeSchema>;

/**
 * Server action to handle email subscription
 */
export async function subscribeToNewsletter(formData: FormData) {
  // Safety: validate form data against schema
  const validatedFields = SubscribeSchema.safeParse({
    email: formData.get('email'),
    name: formData.get('name'),
    marketingConsent: formData.get('marketingConsent') === 'on',
  });

  // Return early if validation fails
  if (!validatedFields.success) {
    return {
      success: false,
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  // Destructure validated data
  const { email, name, marketingConsent } = validatedFields.data;

  try {
    // This would be an API call to your backend
    // For now, we'll just simulate a delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Set a cookie to remember the user's email
    cookies().set('subscribedEmail', email, {
      httpOnly: true,
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 30, // 30 days
    });

    // Revalidate the current path to refresh server components
    revalidatePath('/');

    // Return success response
    return { success: true };
  } catch (error) {
    // Return error response
    return {
      success: false,
      message: 'Something went wrong. Please try again.',
    };
  }
}

/**
 * Server action to handle contact form submission
 */
export async function submitContactForm(formData: FormData) {
  // Simulate processing delay
  await new Promise((resolve) => setTimeout(resolve, 1500));

  // Here you would typically send this data to your API
  // For demo purposes, we'll just redirect
  redirect('/contact/thank-you');
}
