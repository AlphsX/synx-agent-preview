import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class'],
  theme: {
  	extend: {
  		fontFamily: {
  			sans: [
  				'var(--font-inter)',
  				'system-ui',
  				'sans-serif'
  			]
  		},
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			gray: {
  				'50': 'hsl(var(--gray-50))',
  				'100': 'hsl(var(--gray-100))',
  				'200': 'hsl(var(--gray-200))',
  				'300': 'hsl(var(--gray-300))',
  				'400': 'hsl(var(--gray-400))',
  				'500': 'hsl(var(--gray-500))',
  				'600': 'hsl(var(--gray-600))',
  				'700': 'hsl(var(--gray-700))',
  				'800': 'hsl(var(--gray-800))',
  				'850': 'hsl(var(--gray-850))',
  				'900': 'hsl(var(--gray-900))',
  				'950': 'hsl(var(--gray-950))',
  				'1000': 'hsl(var(--gray-1000))'
  			},
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		animation: {
  			'fade-in': 'fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
  			'fade-in-up': 'fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
  			'slide-up': 'slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
  			'slide-down': 'slideDown 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
  			'slide-in': 'slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  			'slide-in-left': 'slideInLeft 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  			'slide-out-left': 'slideOutLeft 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  			'collapse-width': 'collapseWidth 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  			'expand-width': 'expandWidth 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  			'scale-in': 'scaleIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  			shimmer: 'shimmer 2s infinite',
  			gradient: 'gradient 4s ease infinite',
  			bounce: 'bounce 1s infinite',
  			pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'notification-enter': 'notificationEnter 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'notification-exit': 'notificationExit 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'luxury-pulse': 'luxuryPulse 2s ease-in-out infinite'
  		},
  		keyframes: {
  			fadeIn: {
  				'0%': {
  					opacity: '0'
  				},
  				'100%': {
  					opacity: '1'
  				}
  			},
  			fadeInUp: {
  				'0%': {
  					opacity: '0',
  					transform: 'translateY(20px)'
  				},
  				'100%': {
  					opacity: '1',
  					transform: 'translateY(0)'
  				}
  			},
  			slideUp: {
  				'0%': {
  					transform: 'translateY(10px)',
  					opacity: '0'
  				},
  				'100%': {
  					transform: 'translateY(0)',
  					opacity: '1'
  				}
  			},
  			slideDown: {
  				'0%': {
  					transform: 'translateY(-10px)',
  					opacity: '0'
  				},
  				'100%': {
  					transform: 'translateY(0)',
  					opacity: '1'
  				}
  			},
  			slideIn: {
  				'0%': {
  					transform: 'translateX(-100%)',
  					opacity: '0'
  				},
  				'100%': {
  					transform: 'translateX(0)',
  					opacity: '1'
  				}
  			},
  			slideInLeft: {
  				'0%': {
  					transform: 'translateX(-100%)'
  				},
  				'100%': {
  					transform: 'translateX(0)'
  				}
  			},
  			slideOutLeft: {
  				'0%': {
  					transform: 'translateX(0)'
  				},
  				'100%': {
  					transform: 'translateX(-100%)'
  				}
  			},
  			collapseWidth: {
  				'0%': {
  					width: '256px'
  				},
  				'100%': {
  					width: '64px'
  				}
  			},
  			expandWidth: {
  				'0%': {
  					width: '64px'
  				},
  				'100%': {
  					width: '256px'
  				}
  			},
  			scaleIn: {
  				'0%': {
  					transform: 'scale(0.95)',
  					opacity: '0'
  				},
  				'100%': {
  					transform: 'scale(1)',
  					opacity: '1'
  				}
  			},
  			shimmer: {
  				'0%': {
  					backgroundPosition: '-200% 0'
  				},
  				'100%': {
  					backgroundPosition: '200% 0'
  				}
  			},
  			gradient: {
  				'0%': {
  					backgroundPosition: '0% 50%'
  				},
  				'50%': {
  					backgroundPosition: '100% 50%'
  				},
  				'100%': {
  					backgroundPosition: '0% 50%'
  				}
  			},
  			bounce: {
  				'0%, 100%': {
  					transform: 'translateY(0)',
  					animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)'
  				},
  				'50%': {
  					transform: 'translateY(-25%)',
  					animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)'
  				}
  			},
  			pulse: {
  				'0%, 100%': {
  					opacity: '1'
  				},
  				'50%': {
  					opacity: '0.5'
  				}
  			},
        notificationEnter: {
          '0%': {
            transform: 'translateY(-100%) scale(0.8)',
            opacity: '0'
          },
          '100%': {
            transform: 'translateY(0) scale(1)',
            opacity: '1'
          }
        },
        notificationExit: {
          '0%': {
            transform: 'translateY(0) scale(1)',
            opacity: '1'
          },
          '100%': {
            transform: 'translateY(-100%) scale(0.8)',
            opacity: '0'
          }
        },
        luxuryPulse: {
          '0%, 100%': {
            transform: 'scale(1)',
            opacity: '1'
          },
          '50%': {
            transform: 'scale(1.05)',
            opacity: '0.9'
          }
        }
  		},
  		backdropBlur: {
  			xs: '2px'
  		},
  		boxShadow: {
  			soft: '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
  			'soft-lg': '0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
}

export default config