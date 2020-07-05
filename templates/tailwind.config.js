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
            }
        },
    },
    variants: {},
    plugins: [],
}
