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
            backgroundImage: theme => ({
                'hero-image': "url('/static/Aquiles.jpg')",
                'hero-image-square': "url('/static/aquiles_square.jpg')",
            })
        },
        boxShadow: {
            sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            default: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
            link: 'inset 0 -4px 0 0 rgba(178, 245, 234, .7)',
            wikilink: 'inset 0 -4px 0 0 rgba(251, 211, 141, .7)',
            none: 'none',
        },
    },
    variants: {},
    plugins: [],
}
