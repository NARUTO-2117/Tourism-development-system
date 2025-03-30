const path = require('path');

module.exports = {
    entry: './js/index_js.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'dist'),
    },
};  
