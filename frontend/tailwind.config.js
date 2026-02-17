/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      animation: {
        'shimmer': 'shimmer 2s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'elevation-1': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'elevation-2': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'elevation-3': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: theme('colors.gray.700'),
            a: {
              color: theme('colors.primary.600'),
              '&:hover': {
                color: theme('colors.primary.700'),
              },
              textDecoration: 'underline',
              fontWeight: '500',
            },
            'h1, h2, h3, h4, h5, h6': {
              color: theme('colors.gray.900'),
              fontWeight: '600',
            },
            code: {
              color: theme('colors.primary.700'),
              backgroundColor: theme('colors.gray.100'),
              padding: '0.2em 0.4em',
              borderRadius: '0.25rem',
              fontWeight: '500',
            },
            'code::before': {
              content: '""',
            },
            'code::after': {
              content: '""',
            },
            pre: {
              backgroundColor: theme('colors.gray.900'),
              color: theme('colors.gray.100'),
              borderRadius: '0.5rem',
              padding: '1rem',
            },
            'pre code': {
              backgroundColor: 'transparent',
              color: 'inherit',
              padding: '0',
            },
            blockquote: {
              borderLeftColor: theme('colors.primary.500'),
              borderLeftWidth: '4px',
              fontStyle: 'italic',
              color: theme('colors.gray.700'),
              backgroundColor: theme('colors.primary.50'),
              padding: '1rem',
              borderRadius: '0.375rem',
            },
            table: {
              width: '100%',
              borderCollapse: 'collapse',
            },
            'thead th': {
              backgroundColor: theme('colors.primary.100'),
              color: theme('colors.primary.900'),
              fontWeight: '600',
              padding: '0.75rem',
              borderBottom: `2px solid ${theme('colors.primary.300')}`,
            },
            'tbody td': {
              padding: '0.75rem',
              borderBottom: `1px solid ${theme('colors.gray.200')}`,
            },
            'tbody tr:hover': {
              backgroundColor: theme('colors.gray.50'),
            },
            strong: {
              color: theme('colors.gray.900'),
              fontWeight: '700',
            },
            ul: {
              listStyleType: 'disc',
            },
            ol: {
              listStyleType: 'decimal',
            },
            'ul > li': {
              paddingLeft: '0.5rem',
            },
            'ol > li': {
              paddingLeft: '0.5rem',
            },
          },
        },
        invert: {
          css: {
            color: theme('colors.gray.300'),
            a: {
              color: theme('colors.primary.400'),
              '&:hover': {
                color: theme('colors.primary.300'),
              },
            },
            'h1, h2, h3, h4, h5, h6': {
              color: theme('colors.white'),
            },
            code: {
              color: theme('colors.primary.300'),
              backgroundColor: theme('colors.slate.700'),
            },
            pre: {
              backgroundColor: theme('colors.slate.900'),
              color: theme('colors.gray.100'),
            },
            blockquote: {
              borderLeftColor: theme('colors.primary.400'),
              color: theme('colors.gray.300'),
              backgroundColor: theme('colors.slate.700'),
            },
            'thead th': {
              backgroundColor: theme('colors.slate.700'),
              color: theme('colors.primary.300'),
              borderBottomColor: theme('colors.slate.600'),
            },
            'tbody td': {
              borderBottomColor: theme('colors.slate.700'),
            },
            'tbody tr:hover': {
              backgroundColor: theme('colors.slate.700'),
            },
            strong: {
              color: theme('colors.white'),
            },
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
