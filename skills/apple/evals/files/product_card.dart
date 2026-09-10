import 'package:flutter/material.dart';

class ProductCard extends StatefulWidget {
  final List<String> tags;

  ProductCard({required this.tags});

  @override
  State<ProductCard> createState() => _ProductCardState();
}

class _ProductCardState extends State<ProductCard> {
  bool expanded = false;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Row(
            children: [
              Text('Product'),
              Spacer(),
              IconButton(
                icon: Icon(Icons.expand_more),
                onPressed: () => setState(() => expanded = !expanded),
              ),
            ],
          ),
          if (expanded)
            Column(
              children: List.generate(
                widget.tags.length,
                (i) => Text(widget.tags[i]),
              ),
            ),
        ],
      ),
    );
  }
}
