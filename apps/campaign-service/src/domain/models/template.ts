/**
 * Email Template Value Object
 *
 * This represents an email template that can be used in campaigns.
 */

import { TemplateContentType } from '../common/enums';
import { TemplateId, UserId } from '../common/identifiers';

/**
 * Template content
 */
export interface TemplateContent {
  /**
   * Content type
   */
  type: TemplateContentType;

  /**
   * Content body
   */
  body: string;
}

/**
 * Template personalization variable
 */
export interface TemplateVariable {
  /**
   * Variable name
   */
  name: string;

  /**
   * Variable description
   */
  description?: string;

  /**
   * Default value
   */
  defaultValue?: string;

  /**
   * Whether the variable is required
   */
  required?: boolean;
}

/**
 * Email template properties
 */
export interface EmailTemplateProps {
  /**
   * Template ID
   */
  id: TemplateId;

  /**
   * Template name
   */
  name: string;

  /**
   * Template description
   */
  description?: string;

  /**
   * Subject line
   */
  subject: string;

  /**
   * From address
   */
  fromAddress: string;

  /**
   * From name
   */
  fromName?: string;

  /**
   * Reply-to address
   */
  replyTo?: string;

  /**
   * Template contents (multiple formats supported)
   */
  contents: TemplateContent[];

  /**
   * Personalization variables
   */
  variables?: TemplateVariable[];

  /**
   * Template categories
   */
  categories?: string[];

  /**
   * Creator user ID
   */
  createdBy?: UserId;

  /**
   * Creation date
   */
  createdAt?: Date;

  /**
   * Last modified date
   */
  updatedAt?: Date;

  /**
   * Template version
   */
  version?: number;

  /**
   * Additional headers
   */
  headers?: Record<string, string>;

  /**
   * Whether this is a system template
   */
  isSystem?: boolean;
}

/**
 * Email Template Value Object
 */
export class EmailTemplate {
  private readonly _id: TemplateId;
  private readonly _name: string;
  private readonly _description?: string;
  private readonly _subject: string;
  private readonly _fromAddress: string;
  private readonly _fromName?: string;
  private readonly _replyTo?: string;
  private readonly _contents: TemplateContent[];
  private readonly _variables: TemplateVariable[];
  private readonly _categories: string[];
  private readonly _createdBy?: UserId;
  private readonly _createdAt: Date;
  private readonly _updatedAt: Date;
  private readonly _version: number;
  private readonly _headers: Record<string, string>;
  private readonly _isSystem: boolean;

  /**
   * Create a new email template
   * @param props Template properties
   */
  constructor(props: EmailTemplateProps) {
    this._id = props.id;
    this._name = props.name;
    this._description = props.description;
    this._subject = props.subject;
    this._fromAddress = props.fromAddress;
    this._fromName = props.fromName;
    this._replyTo = props.replyTo;
    this._contents = [...props.contents];
    this._variables = props.variables ? [...props.variables] : [];
    this._categories = props.categories ? [...props.categories] : [];
    this._createdBy = props.createdBy;
    this._createdAt = props.createdAt ?? new Date();
    this._updatedAt = props.updatedAt ?? new Date();
    this._version = props.version ?? 1;
    this._headers = props.headers ? { ...props.headers } : {};
    this._isSystem = props.isSystem ?? false;

    this.validate();
  }

  // Getters
  public get id(): TemplateId { return this._id; }
  public get name(): string { return this._name; }
  public get description(): string | undefined { return this._description; }
  public get subject(): string { return this._subject; }
  public get fromAddress(): string { return this._fromAddress; }
  public get fromName(): string | undefined { return this._fromName; }
  public get replyTo(): string | undefined { return this._replyTo; }
  public get contents(): TemplateContent[] { return [...this._contents]; }
  public get variables(): TemplateVariable[] { return [...this._variables]; }
  public get categories(): string[] { return [...this._categories]; }
  public get createdBy(): UserId | undefined { return this._createdBy; }
  public get createdAt(): Date { return new Date(this._createdAt); }
  public get updatedAt(): Date { return new Date(this._updatedAt); }
  public get version(): number { return this._version; }
  public get headers(): Record<string, string> { return { ...this._headers }; }
  public get isSystem(): boolean { return this._isSystem; }

  /**
   * Get the HTML content if available
   */
  public get htmlContent(): string | undefined {
    const html = this._contents.find(c => c.type === TemplateContentType.HTML);
    return html?.body;
  }

  /**
   * Get the text content if available
   */
  public get textContent(): string | undefined {
    const text = this._contents.find(c => c.type === TemplateContentType.TEXT);
    return text?.body;
  }

  /**
   * Validate template configuration
   */
  private validate(): void {
    if (!this._name) {
      throw new Error('Template name is required');
    }

    if (!this._subject) {
      throw new Error('Template subject is required');
    }

    if (!this._fromAddress) {
      throw new Error('Template from address is required');
    }

    // Email address format validation (simple check)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this._fromAddress)) {
      throw new Error('Invalid from address format');
    }

    if (this._replyTo && !emailRegex.test(this._replyTo)) {
      throw new Error('Invalid reply-to address format');
    }

    // Contents validation
    if (this._contents.length === 0) {
      throw new Error('Template must have at least one content type');
    }

    // Check for required content types
    const hasHtml = this._contents.some(c => c.type === TemplateContentType.HTML);
    const hasText = this._contents.some(c => c.type === TemplateContentType.TEXT);

    if (!hasHtml && !hasText) {
      throw new Error('Template must have either HTML or TEXT content');
    }

    // Validate contents
    this._contents.forEach(content => {
      if (!content.body) {
        throw new Error(`Empty content body for type ${content.type}`);
      }
    });

    // Validate variables
    const variableNames = new Set<string>();
    this._variables.forEach(variable => {
      if (!variable.name) {
        throw new Error('Template variable must have a name');
      }

      if (variableNames.has(variable.name)) {
        throw new Error(`Duplicate variable name: ${variable.name}`);
      }

      variableNames.add(variable.name);
    });
  }

  /**
   * Check if the template is valid
   * @returns Whether the template is valid
   */
  public isValid(): boolean {
    try {
      this.validate();
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get all variable names used in the template
   * @returns Array of variable names
   */
  public getVariableNames(): string[] {
    return this._variables.map(v => v.name);
  }

  /**
   * Check if template has a specific content type
   * @param type Content type to check
   * @returns Whether the template has the content type
   */
  public hasContentType(type: TemplateContentType): boolean {
    return this._contents.some(c => c.type === type);
  }

  /**
   * Create a basic template with HTML and text content
   * @param id Template ID
   * @param name Template name
   * @param subject Subject line
   * @param fromAddress From address
   * @param htmlContent HTML content
   * @param textContent Text content
   * @param fromName Optional from name
   * @returns Email template
   */
  public static createBasic(
    id: TemplateId,
    name: string,
    subject: string,
    fromAddress: string,
    htmlContent: string,
    textContent: string,
    fromName?: string
  ): EmailTemplate {
    return new EmailTemplate({
      id,
      name,
      subject,
      fromAddress,
      fromName,
      contents: [
        { type: TemplateContentType.HTML, body: htmlContent },
        { type: TemplateContentType.TEXT, body: textContent },
      ],
    });
  }

  /**
   * Serialize to plain object
   * @returns Plain object representation
   */
  public toJSON(): Record<string, any> {
    return {
      id: this._id.value,
      name: this._name,
      description: this._description,
      subject: this._subject,
      fromAddress: this._fromAddress,
      fromName: this._fromName,
      replyTo: this._replyTo,
      contents: this._contents,
      variables: this._variables,
      categories: this._categories,
      createdBy: this._createdBy?.value,
      createdAt: this._createdAt.toISOString(),
      updatedAt: this._updatedAt.toISOString(),
      version: this._version,
      headers: this._headers,
      isSystem: this._isSystem,
    };
  }
}
