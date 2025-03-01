import { TDShape, TDShapeType } from '@tldraw/tldraw'

/**
 * Types of email content cards available in the editor
 */
export type CardType = 'text' | 'image' | 'button' | 'divider' | 'spacer' | 'product' | 'dynamic'

/**
 * Content type for text cards
 */
export interface TextCardContent {
  text: string
}

/**
 * Style properties for text cards
 */
export interface TextCardStyles {
  fontSize: number
  fontFamily?: string
  color: string
  backgroundColor?: string
  textAlign?: 'left' | 'center' | 'right' | 'justify'
  fontWeight?: 'normal' | 'bold' | string
  fontStyle?: 'normal' | 'italic'
  lineHeight?: number
  padding?: number | { top: number; right: number; bottom: number; left: number }
}

/**
 * Content type for image cards
 */
export interface ImageCardContent {
  src: string
  alt?: string
}

/**
 * Style properties for image cards
 */
export interface ImageCardStyles {
  borderRadius?: number
  border?: string
  objectFit?: 'cover' | 'contain' | 'fill' | 'none'
  boxShadow?: string
}

/**
 * Content type for button cards
 */
export interface ButtonCardContent {
  text: string
  href: string
}

/**
 * Style properties for button cards
 */
export interface ButtonCardStyles {
  backgroundColor: string
  color: string
  fontSize: number
  fontFamily?: string
  borderRadius?: number
  border?: string
  textAlign?: 'left' | 'center' | 'right'
  fontWeight?: 'normal' | 'bold' | string
  width?: number
  padding?: { top: number; right: number; bottom: number; left: number }
}

/**
 * Content type for divider cards
 */
export interface DividerCardContent {
  type?: 'solid' | 'dashed' | 'dotted'
}

/**
 * Style properties for divider cards
 */
export interface DividerCardStyles {
  color: string
  thickness: number
  margin?: { top: number; bottom: number }
}

/**
 * Content type for spacer cards
 */
export interface SpacerCardContent {
  height: number
}

/**
 * Style properties for spacer cards
 * (no specific styles for spacers)
 */
export interface SpacerCardStyles {}

/**
 * Content type for product cards
 */
export interface ProductCardContent {
  title: string
  description?: string
  price: number
  discountPrice?: number
  currency?: string
  imageSrc: string
  productUrl: string
}

/**
 * Style properties for product cards
 */
export interface ProductCardStyles {
  layout: 'vertical' | 'horizontal'
  borderRadius?: number
  padding?: number
  backgroundColor?: string
  titleColor?: string
  descriptionColor?: string
  priceColor?: string
  discountPriceColor?: string
  border?: string
}

/**
 * Content type for dynamic content cards
 */
export interface DynamicCardContent {
  type: 'personalization' | 'condition' | 'loop'
  variable?: string
  condition?: string
  defaultContent?: string
}

/**
 * Style properties for dynamic content cards
 */
export interface DynamicCardStyles {
  backgroundColor?: string
  border?: string
  borderRadius?: number
  padding?: number
}

/**
 * Props for email card shapes in tldraw
 */
export interface EmailCardProps {
  content:
    | TextCardContent
    | ImageCardContent
    | ButtonCardContent
    | DividerCardContent
    | SpacerCardContent
    | ProductCardContent
    | DynamicCardContent
  styles:
    | TextCardStyles
    | ImageCardStyles
    | ButtonCardStyles
    | DividerCardStyles
    | SpacerCardStyles
    | ProductCardStyles
    | DynamicCardStyles
}

/**
 * Shape definition for email cards in tldraw
 */
export interface EmailCardShape extends TDShape {
  type: TDShapeType
  props: EmailCardProps
}

/**
 * Interface for suggestions from AI Assistant
 */
export interface AiSuggestion {
  id: string
  type: 'content' | 'design'
  content: string
  preview?: string
  position?: [number, number]
  changes?: Array<{
    operation: 'create' | 'update' | 'delete'
    shapeId?: string
    properties?: any
    shape?: any
  }>
}

/**
 * Interface for email template metadata
 */
export interface EmailTemplateMetadata {
  id: string
  name: string
  category: string
  thumbnail: string
  description?: string
  tags?: string[]
  isDefault?: boolean
  createdAt: string
  updatedAt: string
}

/**
 * Interface for saved email canvas state
 */
export interface EmailCanvasState {
  id: string
  campaignId: string
  document: any
  lastModified: string
  version: string
  html?: string
}

/**
 * Interface for email canvas export options
 */
export interface EmailExportOptions {
  inlineCss?: boolean
  minify?: boolean
  format?: 'html' | 'json' | 'both'
  includeAnalytics?: boolean
  trackingParams?: Record<string, string>
}

/**
 * Interface for statistics about email elements
 */
export interface EmailCanvasStats {
  textElements: number
  imageElements: number
  buttonElements: number
  dynamicElements: number
  totalElements: number
  estimatedRenderTime: number
  estimatedFileSize: number
  responseCompatibility: {
    desktop: boolean
    mobile: boolean
    outlook: boolean
    gmail: boolean
    apple: boolean
  }
}
