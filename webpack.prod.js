const webpack = require('webpack');
const merge = require('webpack-merge');
const common = require('./webpack.common.js');
const BundleTracker = require('webpack-bundle-tracker');
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');


module.exports = merge(common, {

    plugins: [
        // Todo: Update plugin when deprecation is updated
        new BundleTracker({path: __dirname, filename: 'webpack-stats.json'}),

        // delete all files in build dir automatically
        new CleanWebpackPlugin(['build/dist/']),

        // make sure React strips out debug junk
        // Note: NODE_ENV=production in sh env doesn't trigger this
        // see https://github.com/webpack/webpack/issues/2537
        new webpack.DefinePlugin({
            'process.env': {
                'NODE_ENV': JSON.stringify('production')
            }
        })
    ],

    optimization: {
        minimizer: [
            new UglifyJSPlugin({
                uglifyOptions: {
                    ecma: 5,
                    output: {
                        comments: false
                    },
                    compress: {
                        dead_code: true,
                        drop_console: true
                    }
                },
                sourceMap: false,
            })
        ],
    },

});
