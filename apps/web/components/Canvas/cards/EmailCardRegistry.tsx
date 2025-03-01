import React from 'react'
import { TDShapeType, TldrawApp, HTMLContainer, TDShape } from '@tldraw/tldraw'
import { CardType, TextCardContent, TextCardStyles,
  ImageCardContent, ImageCardStyles, ButtonCardContent, ButtonCardStyles,
  DividerCardContent, DividerCardStyles, ProductCardContent, ProductCardStyles,
  DynamicCardContent, DynamicCardStyles, EmailCardShape } from './types'

/**
 * Registry for email-specific card components and shapes for tldraw
 */
export class EmailCardRegistry {
  /**
   * Register all email card shapes with the tldraw app
   */
  static registerShapes(app: TldrawApp) {
    this.registerTextCardShape(app)
    this.registerImageCardShape(app)
    this.registerButtonCardShape(app)
    this.registerDividerCardShape(app)
    this.registerSpacerCardShape(app)
    this.registerProductCardShape(app)
    this.registerDynamicCardShape(app)
  }

  /**
   * Register the text card shape
   */
  private static registerTextCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-text',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-text' as TDShapeType,
          name: 'Text Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [300, 100],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 1,
          props: {
            content: props.props?.content || { text: 'Enter your text here' },
            styles: props.props?.styles || { fontSize: 16, color: '#000000' }
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const content = shape.props.content as TextCardContent
        const styles = shape.props.styles as TextCardStyles

        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                padding: '8px',
                fontSize: `${styles.fontSize}px`,
                fontFamily: styles.fontFamily || 'inherit',
                color: styles.color,
                backgroundColor: styles.backgroundColor || 'transparent',
                textAlign: styles.textAlign || 'left',
                fontWeight: styles.fontWeight || 'normal',
                fontStyle: styles.fontStyle || 'normal',
                lineHeight: styles.lineHeight ? `${styles.lineHeight}px` : 'normal',
                overflow: 'hidden',
                wordBreak: 'break-word'
              }}
            >
              {content.text}
            </div>
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            rx={4}
            ry={4}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }

  /**
   * Register the image card shape
   */
  private static registerImageCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-image',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-image' as TDShapeType,
          name: 'Image Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [300, 200],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 1,
          props: {
            content: props.props?.content || {
              src: '/placeholder-image.jpg',
              alt: 'Placeholder image'
            },
            styles: props.props?.styles || {
              borderRadius: 0,
              objectFit: 'contain'
            }
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const content = shape.props.content as ImageCardContent
        const styles = shape.props.styles as ImageCardStyles

        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                overflow: 'hidden',
                borderRadius: styles.borderRadius ? `${styles.borderRadius}px` : '0',
                border: styles.border || 'none',
                boxShadow: styles.boxShadow || 'none'
              }}
            >
              <img
                src={content.src}
                alt={content.alt || ''}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: styles.objectFit || 'contain'
                }}
              />
            </div>
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const styles = shape.props.styles as ImageCardStyles
        const borderRadius = styles.borderRadius || 0

        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            rx={borderRadius}
            ry={borderRadius}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }

  /**
   * Register the button card shape
   */
  private static registerButtonCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-button',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-button' as TDShapeType,
          name: 'Button Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [200, 50],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 1,
          props: {
            content: props.props?.content || {
              text: 'Click here',
              href: '#'
            },
            styles: props.props?.styles || {
              backgroundColor: '#0070f3',
              color: '#ffffff',
              fontSize: 16,
              borderRadius: 4,
              textAlign: 'center',
              fontWeight: 'bold'
            }
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const content = shape.props.content as ButtonCardContent
        const styles = shape.props.styles as ButtonCardStyles

        // Calculate padding
        const padding = styles.padding || { top: 8, right: 16, bottom: 8, left: 16 }
        const paddingStyle = `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`

        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: styles.textAlign === 'left' ? 'flex-start' :
                                styles.textAlign === 'right' ? 'flex-end' : 'center',
                alignItems: 'center'
              }}
            >
              <div
                style={{
                  backgroundColor: styles.backgroundColor,
                  color: styles.color,
                  fontSize: `${styles.fontSize}px`,
                  fontFamily: styles.fontFamily || 'inherit',
                  borderRadius: styles.borderRadius ? `${styles.borderRadius}px` : '0',
                  padding: paddingStyle,
                  border: styles.border || 'none',
                  width: styles.width ? `${styles.width}px` : 'auto',
                  textAlign: styles.textAlign || 'center',
                  fontWeight: styles.fontWeight || 'normal',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {content.text}
              </div>
            </div>
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const styles = shape.props.styles as ButtonCardStyles
        const borderRadius = styles.borderRadius || 0

        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            rx={borderRadius}
            ry={borderRadius}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }

  /**
   * Register the divider card shape
   */
  private static registerDividerCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-divider',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-divider' as TDShapeType,
          name: 'Divider Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [400, 10],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 1,
          props: {
            content: props.props?.content || { type: 'solid' },
            styles: props.props?.styles || {
              color: '#e0e0e0',
              thickness: 1,
              margin: { top: 0, bottom: 0 }
            }
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const content = shape.props.content as DividerCardContent
        const styles = shape.props.styles as DividerCardStyles

        const margin = styles.margin || { top: 0, bottom: 0 }
        const lineStyle = content.type || 'solid'

        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                padding: `${margin.top}px 0 ${margin.bottom}px 0`
              }}
            >
              <hr
                style={{
                  width: '100%',
                  height: `${styles.thickness}px`,
                  backgroundColor: styles.color,
                  border: 'none',
                  borderTop: `${styles.thickness}px ${lineStyle} ${styles.color}`
                }}
              />
            </div>
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }

  /**
   * Register the spacer card shape
   */
  private static registerSpacerCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-spacer',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-spacer' as TDShapeType,
          name: 'Spacer Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [400, 50],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 0.5, // More transparent by default
          props: {
            content: props.props?.content || { height: 50 },
            styles: props.props?.styles || {}
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                background: 'repeating-linear-gradient(45deg, rgba(0,0,0,0.03), rgba(0,0,0,0.03) 10px, rgba(0,0,0,0.05) 10px, rgba(0,0,0,0.05) 20px)'
              }}
            />
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }

  /**
   * Register the product card shape
   */
  private static registerProductCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-product',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-product' as TDShapeType,
          name: 'Product Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [400, 300],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 1,
          props: {
            content: props.props?.content || {
              title: 'Product Name',
              description: 'Product description',
              price: 99.99,
              currency: 'USD',
              imageSrc: '/placeholder-product.jpg',
              productUrl: '#'
            },
            styles: props.props?.styles || {
              layout: 'vertical',
              borderRadius: 4,
              padding: 16,
              backgroundColor: '#ffffff',
              titleColor: '#000000',
              descriptionColor: '#666666',
              priceColor: '#000000',
              discountPriceColor: '#ff0000'
            }
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const content = shape.props.content as ProductCardContent
        const styles = shape.props.styles as ProductCardStyles

        const isHorizontal = styles.layout === 'horizontal'
        const formattedPrice = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: content.currency || 'USD'
        }).format(content.price)

        const formattedDiscountPrice = content.discountPrice
          ? new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: content.currency || 'USD'
            }).format(content.discountPrice)
          : null

        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: isHorizontal ? 'row' : 'column',
                backgroundColor: styles.backgroundColor || '#ffffff',
                borderRadius: styles.borderRadius ? `${styles.borderRadius}px` : '0',
                border: styles.border || 'none',
                padding: `${styles.padding || 16}px`,
                overflow: 'hidden'
              }}
            >
              <div
                style={{
                  flex: isHorizontal ? '0 0 40%' : '0 0 auto',
                  maxHeight: isHorizontal ? '100%' : '60%',
                  marginRight: isHorizontal ? '16px' : '0',
                  marginBottom: isHorizontal ? '0' : '16px',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}
              >
                <img
                  src={content.imageSrc}
                  alt={content.title}
                  style={{
                    maxWidth: '100%',
                    maxHeight: '100%',
                    objectFit: 'contain'
                  }}
                />
              </div>
              <div style={{ flex: '1' }}>
                <h3
                  style={{
                    margin: '0 0 8px 0',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    color: styles.titleColor || '#000000'
                  }}
                >
                  {content.title}
                </h3>
                {content.description && (
                  <p
                    style={{
                      margin: '0 0 8px 0',
                      fontSize: '14px',
                      color: styles.descriptionColor || '#666666'
                    }}
                  >
                    {content.description}
                  </p>
                )}
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  {formattedDiscountPrice ? (
                    <>
                      <span
                        style={{
                          fontSize: '16px',
                          fontWeight: 'bold',
                          color: styles.discountPriceColor || '#ff0000',
                          marginRight: '8px'
                        }}
                      >
                        {formattedDiscountPrice}
                      </span>
                      <span
                        style={{
                          fontSize: '14px',
                          textDecoration: 'line-through',
                          color: styles.priceColor || '#000000'
                        }}
                      >
                        {formattedPrice}
                      </span>
                    </>
                  ) : (
                    <span
                      style={{
                        fontSize: '16px',
                        fontWeight: 'bold',
                        color: styles.priceColor || '#000000'
                      }}
                    >
                      {formattedPrice}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const styles = shape.props.styles as ProductCardStyles
        const borderRadius = styles.borderRadius || 0

        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            rx={borderRadius}
            ry={borderRadius}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }

  /**
   * Register the dynamic card shape
   */
  private static registerDynamicCardShape(app: TldrawApp) {
    app.registerShapeType({
      type: 'email-dynamic',
      getShape: (props: any) => {
        return {
          id: props.id,
          type: 'email-dynamic' as TDShapeType,
          name: 'Dynamic Content Block',
          parentId: props.parentId || 'page',
          childIndex: props.childIndex || 1,
          point: props.point || [0, 0],
          size: props.size || [400, 100],
          rotation: props.rotation || 0,
          isLocked: props.isLocked || false,
          opacity: props.opacity || 1,
          props: {
            content: props.props?.content || {
              type: 'personalization',
              variable: 'user.firstName',
              defaultContent: 'Hello there'
            },
            styles: props.props?.styles || {
              backgroundColor: '#f0f9ff',
              border: '1px dashed #0070f3',
              borderRadius: 4,
              padding: 8
            }
          }
        } as EmailCardShape
      },
      Component: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const content = shape.props.content as DynamicCardContent
        const styles = shape.props.styles as DynamicCardStyles

        // Dynamic content display
        let displayLabel = ''
        let displayContent = content.defaultContent || ''

        if (content.type === 'personalization') {
          displayLabel = `Personalized: ${content.variable}`
        } else if (content.type === 'condition') {
          displayLabel = `Conditional: ${content.condition}`
        } else if (content.type === 'loop') {
          displayLabel = `Loop: ${content.variable}`
        }

        return (
          <HTMLContainer>
            <div
              style={{
                width: '100%',
                height: '100%',
                backgroundColor: styles.backgroundColor || '#f0f9ff',
                border: styles.border || '1px dashed #0070f3',
                borderRadius: styles.borderRadius ? `${styles.borderRadius}px` : '0',
                padding: `${styles.padding || 8}px`,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 'bold',
                  marginBottom: '4px',
                  color: '#0070f3'
                }}
              >
                {displayLabel}
              </div>
              <div
                style={{
                  fontSize: '14px',
                  color: '#333333'
                }}
              >
                {displayContent}
              </div>
            </div>
          </HTMLContainer>
        )
      },
      Indicator: (props: { shape: EmailCardShape }) => {
        const { shape } = props
        const styles = shape.props.styles as DynamicCardStyles
        const borderRadius = styles.borderRadius || 0

        return (
          <rect
            x={0}
            y={0}
            width={shape.size[0]}
            height={shape.size[1]}
            rx={borderRadius}
            ry={borderRadius}
            fill="none"
            strokeWidth={2}
            stroke="var(--color-text)"
          />
        )
      }
    })
  }
}
