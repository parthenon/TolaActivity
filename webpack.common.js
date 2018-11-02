const path = require('path');
const webpack = require('webpack');
// const MiniCssExtractPlugin = require("mini-css-extract-plugin");

// To find which plugin(s) is causing DeprecationWarning(s)
// process.traceDeprecation = true;

module.exports = {

    entry: {
        program_page: './js/program_page.js' ,
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
            // {
            //     test: /\.css$/,
            //     use: ['style-loader', MiniCssExtractPlugin.loader, 'css-loader']
            // },
            // {
            //     test: /\.(eot|woff|woff2|ttf|svg|png|jpg)?$/,
            //     use: [{
            //         loader: 'file-loader',
            //         options: {
            //             name: '[name]-[hash].[ext]'
            //         }
            //     }]
            // }
        ]
    },

    resolve: {
        extensions: ['*', '.js', '.jsx']
    },

    plugins: [
        // helps avoid chunkhash changing on bundles w/ no mods
        new webpack.HashedModuleIdsPlugin(),

        // css to their own files
        // new MiniCssExtractPlugin({filename: '[name]-[contenthash].css', allChunks: true}),

        // new webpack.ProvidePlugin({
        //     jQuery: 'jquery',
        //     $: 'jquery',
        //     jquery: 'jquery'
        // }),
    ],
};
