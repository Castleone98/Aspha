package com.example.joljak.comm

import java.io.Serializable

data class SearchResponse(
    val status: String,
    val cars: List<CarData>
) : Serializable

data class CarData(
    val id: Int,
    val names: List<String>,
    val fuelType: String // 연료 타입 필드 추가
) : Serializable


data class CarNameWithFuelType(
    val name: String,
    val fuelType: String,
    var imageUrl : String? = null
)

data class NaverSearchResponse(
    val lastBuildDate: String,
    val total: Int,
    val start: Int,
    val display: Int,
    val items: List<Item>
)

data class Item(
    val title: String,
    val link: String,
    val thumbnail: String,
    val sizeheight: String,
    val sizewidth: String
)