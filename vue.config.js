module.exports = {
    devServer: {
        port: process.env.PORT || 3000,  // Bruk miljøvariabelen, som Azure setter til 80 i produksjon
        proxy: 'http://localhost:8080',  // Proxy API requests til backend
    },
    configureWebpack: {
        devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map',
    },
};
