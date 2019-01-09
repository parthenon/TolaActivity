const path = require('path');
const webpack = require('webpack');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

// To find which plugin(s) is causing DeprecationWarning(s)
// process.traceDeprecation = true;

module.exports = {

    entry: {
        base: './js/base.js',
        program_page: './js/pages/program_page/index.js' ,
    },

    output: {
        filename: "[name]-[chunkhash].js",
        path: path.resolve(__dirname, './build/dist/'),
    },

    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader'
                },

            },
            {
                test: /\.s?[ac]ss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    {loader: 'css-loader', options: {url: true, sourceMap: true}},
                    {loader: 'sass-loader', options: {sourceMap: true}}
                ],
            },
            {
                test: /\.(eot|woff|woff2|ttf|svg|png|jpg|gif)$/,
                use: [{
                    loader: 'file-loader',
                    options: {
                        name: '[name]-[hash].[ext]'
                    }
                }]
            }
        ]
    },

    resolve: {
        extensions: ['*', '.js', '.jsx']
    },

    plugins: [
        // helps avoid chunkhash changing on bundles w/ no mods
        new webpack.HashedModuleIdsPlugin(),

        // css to their own files
        new MiniCssExtractPlugin({filename: '[name]-[contenthash].css'}),

        // new webpack.ProvidePlugin({
        //     jQuery: 'jquery',
        //     $: 'jquery',
        //     jquery: 'jquery',
        // }),
    ],

    externals: {
        jquery: 'jQuery',
    }
};
