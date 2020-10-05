module.exports = {
    purge: {
        enabled: true,
        content: [
            './*.html',
        ],
    },
    theme: {
        extend: {
            fontFamily: {
                serif: ['Playfair Display'],
                sans: ['Poppins'],
                head: ['Red Hat Text, sans-serif'],
                brand: ['Raleway'],
            },
            boxShadow: {
                link: '0 -4px 0 0 rgba(178, 245, 234, .7) inset',
                linkhover: '0 -6px 0 0 rgba(178, 245, 234, .7) inset',
                wikilink: '0 -4px 0 0 rgba(251, 211, 141, .7) inset',
                wikihover: '0 -6px 0 0 rgba(251, 211, 141, .7) inset',
            },
            backgroundImage: theme => ({
                'hero-image': "url('/static/Aquiles.jpg')",
                'hero-image-square': "url('/static/aquiles_square.jpg')",
            }),
        },
        typography: {
            default: {
                css: {
                    a: {
                        'text-decoration': 'none',
                        color: 'inherit',
                    },
                }
            }
        },
    },
    variants: {},
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
