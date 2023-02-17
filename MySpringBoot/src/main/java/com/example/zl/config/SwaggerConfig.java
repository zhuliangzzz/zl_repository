package com.example.zl.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@Configuration
@EnableSwagger2           //开启swagger2
public class SwaggerConfig {
    //配置swagger docket的bean实例
    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
                //  指定构建api文档详细信息的方法
                .apiInfo(apiInfo())
                .select()
                // 指定生成api文档的包路径 这里设置controller生成controller包下的所有接口
                .apis(RequestHandlerSelectors.basePackage("com.example.zl.controller"))
                .paths(PathSelectors.any())
                .build();
    }

    //创建api文档的详细信息
    private ApiInfo apiInfo() {
        return new ApiInfoBuilder()
                .title("springboot集成swagger2接口")
                .description("springboot之swagger")
                //联系方式
                .contact(new Contact("liangzhu", "http://www.baidu.com", "1639329508@qq.com"))
                //版本
                .version("1.0")
                .build();
    }

}
