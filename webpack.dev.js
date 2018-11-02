const path = require('path');
const merge = require('webpack-merge');
const common = require('./webpack.common.js');
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');

module.exports = merge(common, {

    devServer: {
        port: 3032,
        headers: { "Access-Control-Allow-Origin": "*" }
    },

    devtool: 'cheap-module-source-map',

    output: {
        path: path.resolve(__dirname, './build/dev-dist/'),
        publicPath: 'http://localhost:3032/build/dev-dist/'
    },

    plugins: [
        // Todo: Update plugin when deprecation is updated
        new BundleTracker({path: __dirname, filename: 'webpack-stats-dev.json'}),

        // delete all files in static/bundles/ dir automatically
        new CleanWebpackPlugin(['build/dev-dist/']),
    ],
});
