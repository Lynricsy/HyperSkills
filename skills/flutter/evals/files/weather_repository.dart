import 'dart:convert';

import 'package:http/http.dart' as http;

class Weather {
  Weather({required this.city, required this.celsius});

  final String city;
  final double celsius;

  factory Weather.fromJson(Map<String, dynamic> json) => Weather(
        city: json['city'] as String,
        celsius: (json['celsius'] as num).toDouble(),
      );
}

class WeatherException implements Exception {
  WeatherException(this.statusCode);
  final int statusCode;
}

class WeatherRepository {
  WeatherRepository({required http.Client client}) : _client = client;

  final http.Client _client;

  Future<Weather> fetch(String city) async {
    final response = await _client.get(
      Uri.https('api.example.com', '/weather', {'city': city}),
    );
    if (response.statusCode != 200) {
      throw WeatherException(response.statusCode);
    }
    return Weather.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }
}
