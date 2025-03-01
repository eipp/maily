con/**
 * EmailAddress value object
 */
export class EmailAddress {
  private readonly value: string;

  private constructor(value: string) {
    this.value = value;
  }

  /**
   * Create a new EmailAddress instance
   * @param email Email address string
   */
  public static create(email: string): EmailAddress {
    if (!this.isValid(email)) {
      throw new Error(`Invalid email address: ${email}`);
    }

    return new EmailAddress(email);
  }

  /**
   * Validate email format
   * @param email Email address to validate
   */
  public static isValid(email: string): boolean {
    const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return regex.test(email);
  }

  /**
   * Get email value
   */
  public getValue(): string {
    return this.value;
  }

  /**
   * Get domain part of email
   */
  public getDomain(): string {
    return this.value.split('@')[1];
  }

  /**
   * Get local part of email (before @)
   */
  public getLocalPart(): string {
    return this.value.split('@')[0];
  }

  /**
   * Check if email is equal to another email
   * @param other Other email address to compare
   */
  public equals(other: EmailAddress): boolean {
    return this.value.toLowerCase() === other.getValue().toLowerCase();
  }

  /**
   * String representation of the email address
   */
  public toString(): string {
    return this.value;
  }
}
