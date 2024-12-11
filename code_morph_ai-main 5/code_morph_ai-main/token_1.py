import tiktoken
import streamlit as st
# Load the tokenizer for a specific model (e.g., gpt-3.5-turbo)
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

# Sample text data
text_data = """ 
Sure! Let's start by converting the provided PL/SQL code into a Java/Spring Boot application using Domain-Driven Design (DDD) principles. We'll follow the steps outlined to ensure a complete and well-structured codebase.

Step 1: Identify the main functionalities and data structures in the PL/SQL code
The PL/SQL code involves:

Creating tables for entities like Card, Customer, Employee, Branch, Location, Rent, Book, and Video.
Inserting data into these tables.
Procedures for operations like login, view item, account management, renting items, paying fines, updating information, adding customers, etc.
Triggers for certain operations like adding a card upon inserting a customer or employee.
Functions and procedures to handle various business logic.
Step 2: Map PL/SQL procedures and functions to Java methods
We'll create Java classes for the entities, repositories for data access, services for business logic, and controllers for REST API endpoints.

Step 3: Convert PL/SQL data types to appropriate Java data types
We'll map the PL/SQL data types to corresponding Java data types:

NUMBER to Long or Integer
VARCHAR2 to String
DATE to LocalDate
Step 4: Implement database operations using Spring Data JPA
We'll use Spring Data JPA to handle database operations.

Step 5: Use Exception handling
We'll implement exception handling using custom exceptions and Spring's @ExceptionHandler.

Step 6: Apply DDD concepts and microservices architecture
We'll identify bounded contexts and create separate microservices for each context. We'll define domain entities, value objects, aggregates, repositories, and use domain events for communication.

Project Structure
src
├── main
│   ├── java
│   │   └── com
│   │       └── example
│   │           └── library
│   │               ├── config
│   │               ├── controller
│   │               ├── entity
│   │               ├── exception
│   │               ├── repository
│   │               ├── service
│   │               └── LibraryApplication.java
│   └── resources
│       ├── application.properties
│       └── data.sql
└── test
    └── java
        └── com
            └── example
                └── library
                    └── LibraryApplicationTests.java

Step 7: Provide the complete code
Let's start with the application.properties file for database configuration:

# src/main/resources/application.properties

spring.datasource.url=jdbc:h2:mem:testdb
spring.datasource.driverClassName=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=password
spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
spring.h2.console.enabled=true
spring.h2.console.path=/h2-console
spring.jpa.hibernate.ddl-auto=update

Entity Classes
// src/main/java/com/example/library/entity/Card.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
public class Card {
    @Id
    private Long cardID;

    @Column(nullable = false)
    private String status; // 'A' or 'B'

    private Double fines;
}

// src/main/java/com/example/library/entity/Customer.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDate;

@Data
@Entity
public class Customer {
    @Id
    private Long customerID;

    private String name;
    private String customerAddress;
    private Integer phone;
    private String password;
    private String userName;
    private LocalDate dateSignUp;

    @ManyToOne
    @JoinColumn(name = "cardNumber")
    private Card card;
}

// src/main/java/com/example/library/entity/Employee.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
public class Employee {
    @Id
    private Long employeeID;

    private String name;
    private String employeeAddress;
    private Integer phone;
    private String password;
    private String userName;
    private Double paycheck;

    @ManyToOne
    @JoinColumn(name = "branchName")
    private Branch branch;

    @ManyToOne
    @JoinColumn(name = "cardNumber")
    private Card card;
}

// src/main/java/com/example/library/entity/Branch.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
public class Branch {
    @Id
    private String name;

    private String address;
    private Integer phone;
}

// src/main/java/com/example/library/entity/Location.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
public class Location {
    @Id
    private String address;
}

// src/main/java/com/example/library/entity/Rent.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDate;

@Data
@Entity
public class Rent {
    @EmbeddedId
    private RentId id;

    private LocalDate appropriationDate;
    private LocalDate returnDate;
}

// src/main/java/com/example/library/entity/RentId.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.Embeddable;
import java.io.Serializable;

@Data
@Embeddable
public class RentId implements Serializable {
    private Long cardID;
    private String itemID;
}

// src/main/java/com/example/library/entity/Book.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
public class Book {
    @EmbeddedId
    private BookId id;

    private String state;
    private String availability; // 'A' or 'O'
    private Double debyCost;
    private Double lostCost;

    @ManyToOne
    @JoinColumn(name = "address")
    private Location location;
}

// src/main/java/com/example/library/entity/BookId.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.Embeddable;
import java.io.Serializable;

@Data
@Embeddable
public class BookId implements Serializable {
    private String ISBN;
    private String bookID;
}

// src/main/java/com/example/library/entity/Video.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
public class Video {
    @EmbeddedId
    private VideoId id;

    private String state;
    private String availability; // 'A' or 'O'
    private Double debyCost;
    private Double lostCost;

    @ManyToOne
    @JoinColumn(name = "address")
    private Location location;
}

// src/main/java/com/example/library/entity/VideoId.java
package com.example.library.entity;

import lombok.Data;
import javax.persistence.Embeddable;
import java.io.Serializable;

@Data
@Embeddable
public class VideoId implements Serializable {
    private String title;
    private Integer year;
    private String videoID;
}

Repositories
// src/main/java/com/example/library/repository/CardRepository.java
package com.example.library.repository;

import com.example.library.entity.Card;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CardRepository extends JpaRepository<Card, Long> {
}

// src/main/java/com/example/library/repository/CustomerRepository.java
package com.example.library.repository;

import com.example.library.entity.Customer;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CustomerRepository extends JpaRepository<Customer, Long> {
    Customer findByUserName(String userName);
}

// src/main/java/com/example/library/repository/EmployeeRepository.java
package com.example.library.repository;

import com.example.library.entity.Employee;
import org.springframework.data.jpa.repository.JpaRepository;

public interface EmployeeRepository extends JpaRepository<Employee, Long> {
    Employee findByUserName(String userName);
}

// src/main/java/com/example/library/repository/BranchRepository.java
package com.example.library.repository;

import com.example.library.entity.Branch;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BranchRepository extends JpaRepository<Branch, String> {
}

// src/main/java/com/example/library/repository/LocationRepository.java
package com.example.library.repository;

import com.example.library.entity.Location;
import org.springframework.data.jpa.repository.JpaRepository;

public interface LocationRepository extends JpaRepository<Location, String> {
}

// src/main/java/com/example/library/repository/RentRepository.java
package com.example.library.repository;

import com.example.library.entity.Rent;
import com.example.library.entity.RentId;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RentRepository extends JpaRepository<Rent, RentId> {
}

// src/main/java/com/example/library/repository/BookRepository.java
package com.example.library.repository;

import com.example.library.entity.Book;
import com.example.library.entity.BookId;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookRepository extends JpaRepository<Book, BookId> {
}

// src/main/java/com/example/library/repository/VideoRepository.java
package com.example.library.repository;

import com.example.library.entity.Video;
import com.example.library.entity.VideoId;
import org.springframework.data.jpa.repository.JpaRepository;

public interface VideoRepository extends JpaRepository<Video, VideoId> {
}

Service Layer
// src/main/java/com/example/library/service/CustomerService.java
package com.example.library.service;

import com.example.library.entity.Customer;
import com.example.library.repository.CustomerRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class CustomerService {
    @Autowired
    private CustomerRepository customerRepository;

    public Customer login(String userName, String password) {
        Customer customer = customerRepository.findByUserName(userName);
        if (customer != null && customer.getPassword().equals(password)) {
            return customer;
        } else {
            throw new RuntimeException("Incorrect username or password");
        }
    }

    public Customer saveCustomer(Customer customer) {
        return customerRepository.save(customer);
    }
}

// src/main/java/com/example/library/service/EmployeeService.java
package com.example.library.service;

import com.example.library.entity.Employee;
import com.example.library.repository.EmployeeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class EmployeeService {
    @Autowired
    private EmployeeRepository employeeRepository;

    public Employee login(String userName, String password) {
        Employee employee = employeeRepository.findByUserName(userName);
        if (employee != null && employee.getPassword().equals(password)) {
            return employee;
        } else {
            throw new RuntimeException("Incorrect username or password");
        }
    }

    public Employee saveEmployee(Employee employee) {
        return employeeRepository.save(employee);
    }
}

// src/main/java/com/example/library/service/BookService.java
package com.example.library.service;

import com.example.library.entity.Book;
import com.example.library.entity.BookId;
import com.example.library.repository.BookRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BookService {
    @Autowired
    private BookRepository bookRepository;

    public Book getBook(BookId bookId) {
        return bookRepository.findById(bookId).orElse(null);
    }

    public List<Book> getAllBooks() {
        return bookRepository.findAll();
    }

    public Book saveBook(Book book) {
        return bookRepository.save(book);
    }

    public void deleteBook(BookId bookId) {
        bookRepository.deleteById(bookId);
    }
}

// src/main/java/com/example/library/service/VideoService.java
package com.example.library.service;

import com.example.library.entity.Video;
import com.example.library.entity.VideoId;
import com.example.library.repository.VideoRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class VideoService {
    @Autowired
    private VideoRepository videoRepository;

    public Video getVideo(VideoId videoId) {
        return videoRepository.findById(videoId).orElse(null);
    }

    public List<Video> getAllVideos() {
        return videoRepository.findAll();
    }

    public Video saveVideo(Video video) {
        return videoRepository.save(video);
    }

    public void deleteVideo(VideoId videoId) {
        videoRepository.deleteById(videoId);
    }
}

// src/main/java/com/example/library/service/RentService.java
package com.example.library.service;

import com.example.library.entity.*;
import com.example.library.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;

@Service
public class RentService {
    @Autowired
    private RentRepository rentRepository;

    @Autowired
    private BookRepository bookRepository;

    @Autowired
    private VideoRepository videoRepository;

    @Autowired
    private CardRepository cardRepository;

    public Rent rentItem(Long cardID, String itemID, String itemType, LocalDate returnDate) {
        Card card = cardRepository.findById(cardID).orElse(null);
        if (card == null || !card.getStatus().equals("A")) {
            throw new RuntimeException("The user is blocked or card not found");
        }

        if (itemType.equalsIgnoreCase("book")) {
            BookId bookId = new BookId();
            bookId.setBookID(itemID);
            Book book = bookRepository.findById(bookId).orElse(null);
            if (book == null || !book.getAvailability().equals("A")) {
                throw new RuntimeException("The book is already rented or not found");
            }
            book.setAvailability("O");
            bookRepository.save(book);
        } else if (itemType.equalsIgnoreCase("video")) {
            VideoId videoId = new VideoId();
            videoId.setVideoID(itemID);
            Video video = videoRepository.findById(videoId).orElse(null);
            if (video == null || !video.getAvailability().equals("A")) {
                throw new RuntimeException("The video is already rented or not found");
            }
            video.setAvailability("O");
            videoRepository.save(video);
        } else {
            throw new RuntimeException("Invalid item type");
        }

        Rent rent = new Rent();
        RentId rentId = new RentId();
        rentId.setCardID(cardID);
        rentId.setItemID(itemID);
        rent.setId(rentId);
        rent.setAppropriationDate(LocalDate.now());
        rent.setReturnDate(returnDate);
        return rentRepository.save(rent);
    }

    public void returnItem(String itemID) {
        Rent rent = rentRepository.findById(new RentId()).orElse(null);
        if (rent == null) {
            throw new RuntimeException("Item not rented or not found");
        }

        rentRepository.delete(rent);

        BookId bookId = new BookId();
        bookId.setBookID(itemID);
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book != null) {
            book.setAvailability("A");
            bookRepository.save(book);
        }

        VideoId videoId = new VideoId();
        videoId.setVideoID(itemID);
        Video video = videoRepository.findById(videoId).orElse(null);
        if (video != null) {
            video.setAvailability("A");
            videoRepository.save(video);
        }
    }
}

Controller Layer
// src/main/java/com/example/library/controller/CustomerController.java
package com.example.library.controller;

import com.example.library.entity.Customer;
import com.example.library.service.CustomerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/customers")
public class CustomerController {
    @Autowired
    private CustomerService customerService;

    @PostMapping("/login")
    public Customer login(@RequestParam String userName, @RequestParam String password) {
        return customerService.login(userName, password);
    }

    @PostMapping
    public Customer saveCustomer(@RequestBody Customer customer) {
        return customerService.saveCustomer(customer);
    }
}

// src/main/java/com/example/library/controller/EmployeeController.java
package com.example.library.controller;

import com.example.library.entity.Employee;
import com.example.library.service.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/employees")
public class EmployeeController {
    @Autowired
    private EmployeeService employeeService;

    @PostMapping("/login")
    public Employee login(@RequestParam String userName, @RequestParam String password) {
        return employeeService.login(userName, password);
    }

    @PostMapping
    public Employee saveEmployee(@RequestBody Employee employee) {
        return employeeService.saveEmployee(employee);
    }
}

// src/main/java/com/example/library/controller/BookController.java
package com.example.library.controller;

import com.example.library.entity.Book;
import com.example.library.entity.BookId;
import com.example.library.service.BookService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/books")
public class BookController {
    @Autowired
    private BookService bookService;

    @GetMapping("/{isbn}/{bookId}")
    public Book getBook(@PathVariable String isbn, @PathVariable String bookId) {
        BookId bookIdObj = new BookId();
        bookIdObj.setISBN(isbn);
        bookIdObj.setBookID(bookId);
        return bookService.getBook(bookIdObj);
    }

    @GetMapping
    public List<Book> getAllBooks() {
        return bookService.getAllBooks();
    }

    @PostMapping
    public Book saveBook(@RequestBody Book book) {
        return bookService.saveBook(book);
    }

    @DeleteMapping("/{isbn}/{bookId}")
    public void deleteBook(@PathVariable String isbn, @PathVariable String bookId) {
        BookId bookIdObj = new BookId();
        bookIdObj.setISBN(isbn);
        bookIdObj.setBookID(bookId);
        bookService.deleteBook(bookIdObj);
    }
}

// src/main/java/com/example/library/controller/VideoController.java
package com.example.library.controller;

import com.example.library.entity.Video;
import com.example.library.entity.VideoId;
import com.example.library.service.VideoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/videos")
public class VideoController {
    @Autowired
    private VideoService videoService;

    @GetMapping("/{title}/{year}/{videoId}")
    public Video getVideo(@PathVariable String title, @PathVariable Integer year, @PathVariable String videoId) {
        VideoId videoIdObj = new VideoId();
        videoIdObj.setTitle(title);
        videoIdObj.setYear(year);
        videoIdObj.setVideoID(videoId);
        return videoService.getVideo(videoIdObj);
    }

    @GetMapping
    public List<Video> getAllVideos() {
        return videoService.getAllVideos();
    }

    @PostMapping
    public Video saveVideo(@RequestBody Video video) {
        return videoService
"""

# Encode the text to get tokens
tokens = encoding.encode(text_data)
st.write("Tokens:", tokens)
st.write("Number of tokens:", len(tokens))

# Decode tokens back to text (optional)
decoded_text = encoding.decode(tokens)
st.write("Decoded text:", decoded_text)
