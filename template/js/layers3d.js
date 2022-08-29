/*

JQuery plugin 
Structure follows: https://learn.jquery.com/plugins/basic-plugin-creation/

*/
"use strict";


(function($) {
    $.fn.layers3d = function (options, element) {
        element = element || this;
        var layers = new Layers3d(options, element);
        element.set_layer = function(layer) {
            layers.set_layer(layer);
        };
        return layers;
    };

    class Layers3d {
        constructor (options, element) {
            var settings = $.extend({
                // 3d volume
                volume: null,
                // 3d volume shape
                shape: null,
                // initial layer
                layer: null,
            }, options);
            this.settings = settings;
            [this.depth, this.height, this.width] = settings.shape;
            this.binary = new Uint8Array(settings.volume);
            var nbytes = this.binary.length;
            var size = this.depth * this.height * this.width;
            if (size == nbytes) {
                this.greyscale = true;
            } else {
                this.greyscale = false;
                if ( (size * 3) != nbytes) {
                    throw new Error("Only greyscale or RGB supported. " + [size, nbytes]);
                }
            }
            this.layer = settings.layer || (this.depth - 1);
            this.canvas = $('<canvas width="'+this.width+'px" height="'+this.height+'px"/>').appendTo(element);
            this.context = this.canvas[0].getContext("2d");
            this.imgData = this.context.createImageData(this.width, this.height);
            this.imgSize = this.width * this.height;
            this.loadImage();
        };
        set_layer(layer) {
            if (layer<0) {
                throw new Error("layer too small: " + [layer, this.depth]);
            }
            if (layer >= this.depth) {
                throw new Error("layer too big: " + [layer, this.depth]);
            }
            this.layer = layer;
            this.loadImage();
        }
        loadImage() {
            var data = this.imgData.data;
            var binary = this.binary;
            if (this.greyscale) {
                var offset = this.imgSize * this.layer;
                for (var i=0; i<this.imgSize; i++) {
                    var sample = binary[offset + i];
                    var i4 = i * 4;
                    data[i4] = sample;
                    data[i4 + 1] = sample;
                    data[i4 + 2] = sample;
                    data[i4 + 3] = 255;
                }
            } else {
                var offset = 3 * this.imgSize * this.layer;
                for (var i=0; i<this.imgSize; i++) {
                    var i4 = i * 4;
                    var i3 = i * 3;
                    var offset3 = offset + i3;
                    data[i4] = binary[offset3];
                    data[i4 + 1] = binary[offset3 + 1];
                    data[i4 + 2] = binary[offset3 + 2];
                    data[i4 + 3] = 255;
                }
            }
            this.context.putImageData(this.imgData, 0, 0);
        }
    }

})(jQuery);
